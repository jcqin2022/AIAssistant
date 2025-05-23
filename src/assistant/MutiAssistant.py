import os
import json
import inspect
import logging
import asyncio
import re
from typing import List, Dict, Optional
from const import *
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from chat_history import ChatHistory
from .MyAssistant import MyAssistant
from .base_assistant import BaseAssistant

class MultiAssistant(BaseAssistant):
    def __init__(self, chat_history: ChatHistory, config: dict, log: logging.Logger):
        super().__init__(chat_history, config, log)
        self.config = config
        self.log = log
        self.manager_model = None
        self.main_executor = None
        self.manager: MyAssistant= None
        self.scheduler: BaseAssistant = None
        self.works = []
        self.messages = []
        self.context = ""
        self.creator = None

    def set_manager(self, manager: MyAssistant):
        self.manager = manager
    
    def set_scheduler(self, schduler: BaseAssistant):
        self.scheduler = schduler

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
        from ..assist_creator import AssistantCreator
        self.creator = AssistantCreator(self.config, self.log)
        """处理用户问题的主流程"""
        if not self.manager:
            raise ValueError("manager is not set")

        # 第一步：使用deepseek确认意图并生成任务列表
        self.log.info("Step 1: Identifying intent and generating task list...")
        intent_prompt = f"""请分析以下用户问题的意图，并将其分解为具体的任务。
            用户问题：{message}"""
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
        review_prompt = f"""请审查以下任务执行结果，确保它们正确回答了原始问题。如果不正确，请指出原因。
            原始问题：{message}
            任务列表：
            {'\n'.join(f'- {task}' for task in tasks)}

            任务执行结果：
            {json.dumps(task_results, indent=2, ensure_ascii=False)}"""

        reviewed_response = await self._process_manager_task(review_prompt)
        self.log.debug(f"Reviewed response: {reviewed_response}")

        # 第四步：使用deepseek总结最终答案
        self.log.info("Step 4: Generating final answer...")
        summary_prompt = f"""请根据以下信息总结出最终答案回答用户问题：
            用户原始问题：{message}
            任务执行结果：
            {json.dumps(task_results, indent=2, ensure_ascii=False)}
            审查反馈：
            {reviewed_response}"""

        final_answer = await self._process_manager_task(summary_prompt)

        # 更新聊天历史
        self.update_chat_history(message, final_answer)

        return final_answer

    async def aask_with_scheduler(self, question: str) -> str:
        # 第一步：确认意图并生成任务列表
        self.log.info("Step 1: Identifying intent and generating task list...")
        tasks_description = await self.anlyze_requirements(question)
        if not tasks_description:
            return ""
        # 第二步：解析任务并执行
        self.log.info("Step 1.5: Creating workers for each task...")
        tasks_result = await self.execute_tasks(tasks_description)
        if not tasks_result:
            return tasks_description
        # 第三步：审查和修正结果
        # self.log.info("Step 2: Reviewing and refining results...")
        # reviewed_response = await self.review_and_refine_results(tasks_description, tasks_result)
        # 第四步：总结最终答案 
        self.log.info("Step 3: Generating final answer...")
        final_answer = await self.deliver_results(question, tasks_result, tasks_description)
        # 更新聊天历史
        self.update_chat_history(question, final_answer)
        return final_answer

    async def anlyze_requirements(self, question: str) -> str:
        """分析需求"""
        if not self.manager:
            raise ValueError("manager is not set")
        # 第一步：确认意图并生成任务列表
        intent_question = f"""当前阶段一, 首先理解问题并与用户确认，得到准确的意图。
            用户问题：{question}
            如果需要确认或用户输入，按照如下格式：
            确认问题：
            - 选项1: 具体描述
            - 选项2: 具体描述
            如果不需要确认或确认后，继续按下面执行：
            如果需要任务列表，严格按照如下格式生成， 任务数量尽量小：
            工作列表：
            任务1: 执行
            任务2: 测试
            """
        intent_response = await self._process_manager_task(intent_question)
        self.log.debug(f"Intent response: {intent_response}")
        if self.check_req_confirmation(intent_response):
            return ''
        return intent_response
    
    async def execute_tasks(self, tasks_description: str) -> str:
        """执行任务"""
        if not self.scheduler:
            raise ValueError("scheduler is not set")

        tasks_result = ""
        # 解析任务列表
        hasTasks = self.check_task_confirmation(tasks_description)
        if hasTasks:
            tasks_result = await self.scheduler.aask(tasks_description)
        else:
            self.log.info("No tasks found, using default response.")
        return tasks_result
    
    async def review_and_refine_results(self, tasks_description, tasks_result: str) -> str:
        """审查和修正结果"""
        if not self.manager:
            raise ValueError("manager is not set")
        reviewed_response = ""
        # 审查和修正结果
        self.log.info("Step 2: Reviewing and refining results...")
        review_question = f"""请审查以下任务执行结果，确保它们正确回答了原始问题。
            任务列表：
            {tasks_description}
            任务执行结果：
            {tasks_result}"""
        reviewed_response = await self._process_manager_task(review_question)
        self.log.debug(f"Reviewed response: {reviewed_response}")
        return reviewed_response
    
    async def deliver_results(self, question: str, task_result: str, reviewed_response: str) -> str:
        """交付结果"""
        if not self.manager:
            raise ValueError("manager is not set")
        # 总结最终答案
        summary_question = f"""当前阶段二，请根据以下信息总结出最终答案回答用户问题：
            用户原始问题：
            {question}
            任务执行结果：
            {task_result}
            审查反馈：
            {reviewed_response}"""

        final_answer = await self._process_manager_task(summary_question)
        self.log.info(f"Final answer: {final_answer}")
        return final_answer
    
    def _parse_task_list(self, intent_response: str) -> List[str]:
        """从意图响应中解析任务列表"""
        tasks = []
        # Remove <think> sections from intent_response
        intent_response = re.sub(r"<think>.*?</think>", "", intent_response, flags=re.DOTALL)
        lines = intent_response.split('\n')
        task_section = False

        for line in lines:
            line = line.strip()
            if TASK_LIST in line:
                task_section = True
                continue
            if task_section and line.startswith(TASK):  # 以-开头的行表示任务
                tasks.append(line[2:].strip())
            elif task_section and line:  # 非空行但不是以-开头，可能意味着任务列表结束
                break

        return tasks
    
    def _parse_task_list2(self, task_description: str) -> List[str]:
        # Remove <think> sections from intent_response
        task_description = re.sub(r"<think>.*?</think>", "", task_description, flags=re.DOTALL)
        # 匹配任务模式的正则表达式（支持多任务连续匹配）
        task_pattern = re.compile(
            r'^任务\d+:.*?$[\n\r]+^└─ 依赖关系：.*?$',
            re.MULTILINE | re.DOTALL
        )
        tasks = []
        dependencies = []
        # 分割所有任务块
        for task_block in task_pattern.finditer(task_description):
            block = task_block.group(0)
            
            # 提取任务描述行
            task_line = re.search(r'^(任务\d+:.*?)(?=\n|$)', block, re.MULTILINE).group(0)
            tasks.append(task_line.strip())
            
            # 提取依赖描述并解析依赖项
            dep_match = re.search(r'└─ 依赖关系：(.*?)$', block, re.MULTILINE)
            dep_desc = dep_match.group(1).strip() if dep_match else ''
            
            # 从依赖描述中提取任务编号（支持中文数字）
            dep_tasks = re.findall(r'任务\d+', dep_desc)
            dependencies.append(dep_tasks)
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
    
    def check_req_confirmation(self, requirements: str) -> bool:
        """检查确认问题"""
        if not requirements:
            return True
        requirements = re.sub(r"<think>.*?</think>", "", requirements, flags=re.DOTALL)
        # 检查是否有确认问题
        if QUSTION_CONFIRM in requirements:
            return True
        return False    
    
    def check_task_confirmation(self, requirements: str) -> bool:
        """检查是否包含任务列表"""
        if not requirements:
            return True
        requirements = re.sub(r"<think>.*?</think>", "", requirements, flags=re.DOTALL)
        # 检查是否有确认问题
        if TASK_LIST in requirements:
            return True
        return False