from abc import ABC, abstractmethod
from typing import Iterable
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletion
)
import logging

class BaseAssistant(ABC):
    def __init__(self, config: dict, log: logging.Logger):
        self.config = config
        self.log = log

    @abstractmethod
    def ask(self, question: str) -> str:
        pass

    @abstractmethod
    async def aask(self, question:str) -> str:
        pass   