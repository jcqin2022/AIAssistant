from abc import ABC, abstractmethod
from typing import Iterable
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletion
)
import logging

class BaseModel(ABC):
    def __init__(self, config: dict, log: logging.Logger):
        self.config = config
        self.log = log

    @abstractmethod
    def ask(self, question: str) -> str:
        pass

    @abstractmethod
    def ask(self, messages: Iterable[ChatCompletionMessageParam], 
            tools_definitions: Iterable[ChatCompletionToolParam]) -> ChatCompletion:
        pass

    @abstractmethod
    def setup_model(self):
        pass    