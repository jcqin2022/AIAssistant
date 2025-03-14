# In k8s executor, it will inherit from Executor, in which, update base class method list to include its functions, and below methods are overrides except execute(),
# get_prompt(): provide a prompt string to tell openai who are you and what you can do. for base class, just a common user enough.
# get_tool_definition(): provide the function definitions of all methods of current class for openai to call.
# execute_script(): kubectl script string will be as argument, check windows or linux, if windows, use cmd to execute, but for linue, adapt bash and return the result.

import os
import subprocess
from executor import Executor
import logging

class K8sExecutor(Executor):
    def __init__(self, config:dict, log: logging.Logger):
        self.config = config
        self.log = log
        super().__init__()
        self.update_method_list()

    def update_method_list(self):
        self.methods[ "execute_script"] = self.execute_script
        self.methods[ "get_system"] = self.get_system

    def get_prompt(self):
        prompt = self.config.get("PROMPT", None)
        prompt = prompt + " " + (
            "I am a Kubernetes and AWS Assistant. I can execute k8s commands (eg. kubectl, kubectx,...) and AWS CLI commands to provide Kubernetes and AWS-related functionalities. "
            "For security reasons, I am restricted to read-only operations by default. "
            "Any script that attempts to modify or delete cluster resources or AWS resources must be confirmed by the user before execution. "
            "You can perform various tasks such as retrieving cluster information, listing resources, checking resource usage, "
            "and other read-only operations. "
            "On Windows, use cmd to execute scripts, and on Linux, use bash. "
            "Ensure that all operations are safe and do not alter the cluster or AWS resources in any way."
        )
        return prompt
    
    def get_context(self):
        return "This is a kubernets cluster hosted in AWS cloud."

    def get_tool_definition(self):
        return [{
            "type": "function",
            "function": {
                "name": "execute_script",
                "description": "Execute a aws and k8s management script string. If on Windows, use cmd to execute. If on Linux, use bash and return the result.",
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
        if os.name == 'nt':  # Windows
            result = subprocess.run(['cmd', '/c', script], capture_output=True, text=True)
        else:  # Linux
            result = subprocess.run(['bash', '-c', script], capture_output=True, text=True)
        return result.stdout
    
    def get_system(self):
        if os.name == 'nt':  # Windows
            return "Windows"
        else:  # Linux
            return "Linux"