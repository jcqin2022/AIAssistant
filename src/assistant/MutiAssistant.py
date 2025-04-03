import os
import json
import inspect
import logging
import asyncio
from typing import List, Dict, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from chat_history import ChatHistory
from .MyAssistant import MyAssistant
from .base_assistant import BaseAssistant

class MultiAssistant(BaseAssistant):
    def __init__(self, chat_history: ChatHistory, config: dict, log: logging.Logger):
        super().__init__(config, log)
        self.config = config
        self.log = log
        self.chat_history = chat_history
        self.manager_model = None
        self.main_executor = None
        self.manager: MyAssistant= None
        self.works = []
        self.messages = []
        self.context = ""
        self.creator = None

    def setup_manager(self):
        from ..assist_creator import AssistantCreator
        self.creator = AssistantCreator(self.config, self.log)
        self.manager = self.creator.create_manager()


    async def _process_task(self, task: str, context: str, assistant: MyAssistant) -> str:
        """使用指定executor处理单个任务"""
        if not assistant:
            raise ValueError(f"Assistant for task {task} not found")

        # 设置消息
        message = f"""context：{context}
            task：{task}"""
        result = await assistant.aask(message)
        return result
    
    async def _process_manager_task(self, task: str) -> str:
        """使用manager任务"""
        if not self.manager:
            self.log.error("Manager is not set")
            raise ValueError("Manager is not set")

        # 设置消息
        result = await self.manager.aask(task)
        return result

    def ask(self, question):
        return ""
    
    async def aask(self, message: str) -> str:
        """处理用户问题的主流程"""
        if not self.manager:
            raise ValueError("manager is not set")

        # 第一步：使用deepseek确认意图并生成任务列表
        self.log.info("Step 1: Identifying intent and generating task list...")
        intent_prompt = f"""请分析以下用户问题的意图，并将其分解为具体的任务列表。
            用户问题：{message}

            请按照以下格式返回：
            1. 意图分析：[简要分析用户意图]
            2. 任务列表：
            - 任务1
            - 任务2
            ..."""
        intent_response = await self._process_manager_task(intent_prompt)
        self.log.debug(f"Intent response: {intent_response}")

        # 解析任务列表
        tasks = self._parse_task_list(intent_response)
        if not tasks:
            return "无法解析任务列表，请尝试重新表述您的问题。"
        
        # 创建worker字典
        self.log.info("Step 1.5: Creating workers for each task...")
        workers = {}
        for i, task in enumerate(tasks):
            worker_name = f"worker_{i+1}"
            workers[worker_name] = self.creator.create_worker()
        self.log.debug(f"Workers created: {list(workers.keys())}")

        # 第二步：使用worker异步执行任务
        self.log.info("Step 2: Executing tasks asynchronously...")
        task_results = {}

        # 创建所有任务的协程
        task_coroutines = []
        for i, task in enumerate(tasks):
            context = f"原始问题：{message}\n当前任务：{task}\n任务序号：{i+1}/{len(tasks)}"
            task_coroutines.append(self._process_task(task, context, workers[f"worker_{i+1}"]))

        # 并行执行所有任务
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # 处理结果
        for i, (task, result) in enumerate(zip(tasks, results)):
            if isinstance(result, Exception):
                self.log.error(f"Task {i+1} failed: {str(result)}")
                task_results[f"任务{i+1}"] = f"执行失败: {str(result)}"
            else:
                task_results[f"任务{i+1}"] = result

        # 第三步：使用deepseek审查和修正结果
        self.log.info("Step 3: Reviewing and refining results...")
        review_prompt = f"""请审查以下任务执行结果，确保它们正确回答了原始问题。如果不正确，请修改背景信息后重新生成答案。
            原始问题：{message}
            任务列表：
            {'\n'.join(f'- {task}' for task in tasks)}

            任务执行结果：
            {json.dumps(task_results, indent=2, ensure_ascii=False)}

            请按照以下步骤操作：
            1. 评估每个任务结果是否正确
            2. 对于不正确的结果，分析原因并修改背景信息
            3. 重新生成更准确的答案"""

        reviewed_response = await self._process_manager_task(review_prompt)
        self.log.debug(f"Reviewed response: {reviewed_response}")

        # 第四步：使用deepseek总结最终答案
        self.log.info("Step 4: Generating final answer...")
        summary_prompt = f"""请根据以下信息总结出最终答案回答用户问题：
            用户原始问题：{message}
            任务执行结果：
            {json.dumps(task_results, indent=2, ensure_ascii=False)}
            审查反馈：
            {reviewed_response}
            请提供清晰、准确的最终答案。"""

        final_answer = await self._process_manager_task(summary_prompt)

        # 更新聊天历史
        self.chat_history.add_user_message(message)
        self.chat_history.add_ai_message(final_answer)

        return final_answer

    def _parse_task_list(self, intent_response: str) -> List[str]:
        """从意图响应中解析任务列表"""
        tasks = []
        lines = intent_response.split('\n')
        task_section = False

        for line in lines:
            line = line.strip()
            if line.count("任务列表") > 0 :
                task_section = True
                continue
            if task_section and line.startswith("- "):
                tasks.append(line[2:].strip())
            elif task_section and line:  # 非空行但不是以-开头，可能意味着任务列表结束
                break

        return tasks

    def _convert_messages_for_openai(self, messages) -> List[Dict]:
        """转换消息格式为OpenAI API需要的格式"""
        openai_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                openai_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})
            else:
                self.log.warning(f"Unsupported message type: {type(msg)}")
        return openai_messages

    def _check_args(self, function, args) -> bool:
        """验证函数参数是否正确"""
        sig = inspect.signature(function)
        params = sig.parameters

        # 检查是否有额外参数
        for name in args:
            if name not in params:
                return False
        # 检查是否提供了必需参数
        for name, param in params.items():
            if param.default is param.empty and name not in args:
                return False

        return True