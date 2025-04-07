# Manager executor, it will inherit from Executor, in which, update prompt and context only.
import os
import subprocess
from .executor import Executor
import logging
import json

class ManagerExecutor(Executor):
    def __init__(self,config:dict, log: logging.Logger):
        self.config = config
        self.log = log
        super().__init__()
        self.prompt = ""
        self.context = ""

    def get_prompt(self):
        if(self.prompt != ""):
            return self.prompt
        self.prompt = super().get_prompt('mgr_prompt.md')
        return self.prompt
    
    def get_context(self):
        if(self.context != ""):
            return self.context
        self.context = super().get_prompt('mgr_context.md')
        return self.context

    def get_tool_definition(self):
        return []