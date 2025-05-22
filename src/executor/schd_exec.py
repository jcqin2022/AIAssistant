# Scheduler executor, it will inherit from Executor, in which, update prompt and context only.
import asyncio
import os
import subprocess
from typing import List
from .executor import Executor
from ..assistant.base_assistant import BaseAssistant
from ..const import *
import logging
import json

class SchedulerExecutor(Executor):
    def __init__(self,config:dict, log: logging.Logger):
        self.config = config
        self.log = log
        super().__init__()
        self.prompt = ""
        self.context = ""
        self.update_method_list()
        self._create_creator()

    def get_prompt(self):
        if(self.prompt != ""):
            return self.prompt
        self.prompt = super().get_prompt('schd_prompt.md')
        return self.prompt
    
    def get_context(self):
        if(self.context != ""):
            return self.context
        self.context = super().get_prompt('schd_context.md')
        return self.context
    
    def update_method_list(self):
        self.methods[ "execute_single_task"] = self.execute_single_task
        self.methods[ "execute_multiple_tasks"] = self.execute_multiple_tasks

    def is_async(self):
        return True
    
    def get_tool_definition(self):
        return [{
            "type": "function",
            "function": {
                "name": "execute_single_task",
                "description": "Asynchronously execute a task with a task descripton and context, and then return the result.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "task description."
                        },
                        "context": {
                            "type": "string",
                            "description": "The context for the task."
                        }
                    },
                    "required": ["task", "context"]
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "execute_multiple_tasks",
                "description": "Asynchronously execute multiple tasks with a task descripton list and one context, and then return the results in a dictionary, like {task 1:result}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "task description for each task."
                        },
                        "context": {
                            "type": "string",
                            "description": "The context for thalle tasks."
                        }
                    },
                    "required": ["tasks", "context"]
                },
            },
        }]

    async def execute_single_task(self, task: str, context: str) -> str:
        self.log.info(f"Executing single task: {task}")
        self.log.info(f"Executing single task context: {context}")
        worker = self.creator.create_worker()
        result = await self._process_task(task, context, worker)
        self.log.info(f"Task result: {result}")
        return result
        
    
    async def execute_multiple_tasks(self, tasks: List[str], context: str) -> str:
        self.log.info("Executing tasks asynchronously...")
        workers = {}
        try:
            for i, task in enumerate(tasks):
                worker_name = f"worker_{i+1}"
                workers[worker_name] = self.creator.create_worker()
                self.log.debug(f"Workers created: {worker_name}-{task}")

            task_results = ""

            # 创建所有任务的协程
            task_coroutines = []
            for i, task in enumerate(tasks):
                context = f"背景：{context}\n当前任务：{task}\n任务序号：{i+1}/{len(tasks)}"
                task_coroutines.append(self._process_task(task, context, workers[f"worker_{i+1}"]))

            # 并行执行所有任务
            results = await asyncio.gather(*task_coroutines, return_exceptions=True)

            # 处理结果
            for i, (task, result) in enumerate(zip(tasks, results)):
                if isinstance(result, Exception):
                    self.log.error(f"{task} failed: {str(result)}")
                    task_results += f"{TASK}{i}:\n{task}\n{TASK_FAILED}:{result}\n\n"
                else:
                    task_results += f"{TASK}{i}:\n{task}\n{RESULT}:{result}\n\n"
            self.log.info(f"Task results: {task_results}")
            return task_results
        except Exception as e:
            self.log.error(f"Executing multi tasks: {str(e)}")
            return str(e)
    
    async def _process_task(self, task: str, context: str, assistant: BaseAssistant) -> str:
        if not assistant:
            raise ValueError(f"Assistant for task {task} not found")
        try:
            # 设置消息
            message = f"""context：{context}
                task：{task}"""
            result = await assistant.aask(message)
            return result
        except Exception as e:
            self.log.error(f"Processing task {task}: {str(e)}")
            return str(e)
    
    def _create_creator(self):
        from ..assist_creator import AssistantCreator
        self.creator = AssistantCreator(self.config, self.log)