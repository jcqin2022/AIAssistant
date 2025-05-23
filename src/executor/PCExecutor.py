# In PC executor, it will inherit from Executor, in which, update base class method list to include its functions, and below methods are overrides except execute(),
# get_prompt(): provide a prompt string to tell openai who are you and what you can do. for base class, just a common user enough.
# get_tool_definition(): provide the function definitions of all methods of current class for openai to call.
# execute_script(): script string will be as argument, check windows or linux, if windows, use cmd to execute, but for linue, adapt bash and return the result.
import os
import subprocess
from .executor import Executor
import logging
import json

class PCExecutor(Executor):
    def __init__(self,config:dict, log: logging.Logger):
        self.config = config
        self.log = log
        super().__init__()
        self.update_method_list()
        self.prompt = ""
        self.context = ""

    def update_method_list(self):
        self.methods[ "execute_script"] = self.execute_script
        self.methods[ "get_system"] = self.get_system

    def get_prompt(self):
        if(self.prompt != ""):
            return self.prompt
        self.prompt = super().get_prompt('pc_prompt.md')
        return self.prompt
    
    def get_context(self):
        if(self.context != ""):
            return self.context
        self.context = super().get_prompt('pc_context.md')
        return self.context

    def get_tool_definition(self):
        return [{
            "type": "function",
            "function": {
                "name": "execute_script",
                "description": "Execute a script string. If on Windows, use power shell to execute. If on Linux, use bash and return the result.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "script": {
                            "type": "string",
                            "description": "The system script to be executed."
                        }
                    },
                    "required": ["script"]
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_system",
                "description": "Return a string to indicate if it is Windows or Linux system.",
            },
        }]

    def execute_script(self, script):
        self.log.debug(f"Executing script: {script}")
        if os.name == 'nt':  # Windows
            result = subprocess.run(['powershell', '-Command', script], capture_output=True, text=True)
        else:  # Linux
            result = subprocess.run(['bash', '-c', script], capture_output=True, text=True)
        result = result.stdout
        self.log.debug(f"Script result: {result}")
        return result
    
    def get_system(self):
        if os.name == 'nt':  # Windows
            return "Windows"
        else:  # Linux
            return "Linux"