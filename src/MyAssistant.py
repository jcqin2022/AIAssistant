# Create MyAssistant class to access AzureOpenAI service. it will use openai service to do chat completions. During the chat, openai service will call local functions which are defined in executor.
# Property as below:
# executor: it will be set with a specific executor instance.
# Method as below:
# ask(): it can invoke chat completions by input message. the prompt message, tool definitions are got from executor instance. if repose is tool_call, it will call execute() of executor instance with name and parameters. Note, openai may need call execute() multiple times to complete the chat.
# set_executor(): a executor instance will be set.

import os
import json

import inspect
import logging
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from chat_history import ChatHistory
from excutor.executor import Executor
from model.base_model import BaseModel

class MyAssistant:
    def __init__(self, chat_history:ChatHistory, config:dict, log: logging.Logger):
        self.config = config
        self.log = log
        self.chat_history = chat_history
        self.executor = None
        self.model = None
        self.messages = []
        self.context = ""
    
    def set_executor(self, executor: Executor):
        self.executor = executor
    
    def set_model(self, model: BaseModel):
        self.model = model

    def setup_messages(self, message:str):
        try:
            prompt = self.executor.get_prompt()
            context = self.executor.get_context()
            message_template = f"""context：{context}
                question：{message}"""
            messages = [
                SystemMessage(content=prompt),
                *self.chat_history.get_full_history(),
                HumanMessage(
                    content=message_template
                ),
            ]
            return messages
        except Exception as e:
            self.log.error(f"Error setting up messages: {e}")
            return None
        
    def ask(self, message):
        if not self.executor:
            raise ValueError("Executor is not set")
        
        # Pass the function result back to the model for further processing
        tool_definitions = self.executor.get_tool_definition()
        self.messages = self.convert_messages_for_openai(self.setup_messages(message))
        response = self.model.ask(self.messages, tool_definitions)

        # check if GPT wanted to call a function
        while response.choices[0].finish_reason == "tool_calls":
            response_message = response.choices[0].message
            
            # call the function
            function_name = response_message.tool_calls[0].function.name
            function_to_call = self.executor.get_function(function_name)
            if function_to_call is None:
                return "Function not found: " + function_name

            # verify function has correct number of arguments
            function_args = json.loads(response_message.tool_calls[0].function.arguments)
            if self.check_args(function_to_call, function_args) is False:
                return "Invalid number of arguments for function: " + function_name
            function_response=self.executor.execute(function_name, **function_args)
            print(f"Function call: {function_name} with arguments: {function_args}")
            # print(f"Return: {function_response}")

            # send the info on the function call and function response to GPT
            # adding assistant response to messages
            self.messages.append(
                {
                    "role": response_message.role,
                    "function_call": {
                        "name": response_message.tool_calls[0].function.name,
                        "arguments": response_message.tool_calls[0].function.arguments,
                    },
                    "content": None,
                }
            )

            # adding function response to messages
            self.messages.append(
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response

            # print("Messages in next request:")
            # for message in self.messages:
            #     print(message)
            # print()
            response = self.model.ask(self.messages, tool_definitions)

        anwser = response.choices[0].message.content.strip()
        self.chat_history.add_user_message(message)
        self.chat_history.add_ai_message(anwser)
        return anwser
    
    def convert_messages_for_openai(self, messages):
        openai_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                openai_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):  # 假设历史消息中有助手回复
                openai_messages.append({"role": "assistant", "content": msg.content})
            else:
                self.log.warning(f"Unsupported message type: {type(msg)}")
        return openai_messages

    # helper method used to check if the correct arguments are provided to a function
    def check_args(self, function, args):
        sig = inspect.signature(function)
        params = sig.parameters

        # Check if there are extra arguments
        for name in args:
            if name not in params:
                return False
        # Check if the required arguments are provided
        for name, param in params.items():
            if param.default is param.empty and name not in args:
                return False

        return True