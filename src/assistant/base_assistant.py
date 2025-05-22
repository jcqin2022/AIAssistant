from abc import ABC, abstractmethod
from typing import Iterable
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletion
)
import logging
from ..chat_history import ChatHistory
class BaseAssistant(ABC):
    def __init__(self, chat_history: ChatHistory, config: dict, log: logging.Logger):
        self.chat_history = chat_history
        self.config = config
        self.log = log

    @abstractmethod
    def ask(self, question: str) -> str:
        pass

    @abstractmethod
    async def aask(self, question:str) -> str:
        pass  

    def update_chat_history(self, question: str, answer: str):
        self.chat_history.add_user_message(question)
        self.chat_history.add_ai_message(answer) 

    def get_chat_history(self) -> Iterable[ChatCompletionMessageParam]:
        return self.chat_history.get_full_history()