from .base_model import BaseModel

class OpenAI(BaseModel):
    
    def ask(self, question: str) -> str:
        # Implement the logic to interact with OpenAI API here
        # For demonstration, we'll return a dummy response
        return f"Response to: {question}"