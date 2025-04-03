from .base_model import BaseModel
import logging
from openai import AzureOpenAI, AsyncAzureOpenAI
from typing import Iterable
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletion
)

class OpenAI(BaseModel):
    def __init__(self, config: dict, log: logging.Logger):
        super().__init__(config, log)
        self.client = None
        self.client_async = None
        self.model_name = None
        self.setup_model()


    def ask(self, messages: Iterable[ChatCompletionMessageParam], 
            tools_definitions: Iterable[ChatCompletionToolParam]) -> ChatCompletion:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools_definitions,
                tool_choice="auto",
            )
            return response
        except Exception as e:
            self.log.error(f"Error asking question: {e}")
            return None
        
    async def aask(self, messages: Iterable[ChatCompletionMessageParam],
            tools_definitions: Iterable[ChatCompletionToolParam]) -> str:
        try:
            response = await self.client_async.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools_definitions,
                tool_choice="auto",
            )
            return response
        except Exception as e:
            self.log.error(f"Error asking question: {e}")
            return None
    
    
    def setup_model(self):
        try:
            self.client = AzureOpenAI(
                azure_endpoint=self.config["AZURE_OPENAI_ENDPOINT"],  # The base URL for your Azure OpenAI resource. e.g. "https://<your resource name>.openai.azure.com"
                api_key=self.config["AZURE_OPENAI_KEY"],  # The API key for your Azure OpenAI resource.
                api_version=self.config["OPENAI_API_VERSION"],  # This version supports function calling
            )

            self.client_async = AsyncAzureOpenAI(
                azure_endpoint=self.config["AZURE_OPENAI_ENDPOINT"],  # The base URL for your Azure OpenAI resource. e.g. "https://<your resource name>.openai.azure.com"
                api_key=self.config["AZURE_OPENAI_KEY"],  # The API key for your Azure OpenAI resource.
                api_version=self.config["OPENAI_API_VERSION"],  # This version supports function calling
            )

            self.model_name = self.config["MODEL_NAME"] # You need to ensure the version of the model you are using supports the function calling feature
        except Exception as e:
            self.log.error(f"Error setting up model: {e}")
            return None
