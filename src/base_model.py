from abc import ABC, abstractmethod

class BaseModel(ABC):
    
    @abstractmethod
    def ask(self, question: str) -> str:
        pass