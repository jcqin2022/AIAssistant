from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class ChatHistory:
    def __init__(self, config: dict):
        self.config = config
        self.max_history_len = config["MAX_HISTORY_LEN"]
        self.history = [] 
        
    def add_user_message(self, message: str):
        self.history.append(HumanMessage(content=message))
        
    def add_ai_message(self, message: str):
        self.history.append(AIMessage(content=message))
    
    def get_full_history(self) -> list:
        if len(self.history) > self.max_history_len:
            self.history.pop(0)
        return self.history.copy()
    
    def clear_history(self):
        self.history.clear()