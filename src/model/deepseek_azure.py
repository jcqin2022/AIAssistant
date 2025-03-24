# Install the following dependencies: azure.identity and azure-ai-inference
import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

from .base_model import BaseModel
import logging
from openai import AzureOpenAI
from typing import Iterable
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletion
)

class DeepSeek(BaseModel):
    def __init__(self, config: dict, log: logging.Logger):
        super().__init__(config, log)
        self.client = None
        self.model_name = None
        self.setup_model()


    def ask(self, messages: Iterable[ChatCompletionMessageParam], 
            tools_definitions: Iterable[ChatCompletionToolParam]) -> ChatCompletion:
        try:
            response = self.client.complete(
                messages=messages,
                model = self.model_name,
                tools=tools_definitions,
                tool_choice="auto",
                max_tokens=1000
            )
            return response
        except Exception as e:
            self.log.error(f"Error asking question: {e}")
            return None
    
    def setup_model(self):
        try:
            endpoint = self.config["AZURE_DS_ENDPOINT"]
            model_name = self.config["AZURE_DS_NAME"]
            key = self.config["AZURE_DS_KEY"]
            self.client  = ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(key))
            self.model_name = model_name
        except Exception as e:
            self.log.error(f"Error setting up model: {e}")
            return None