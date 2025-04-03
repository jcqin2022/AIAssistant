import logging
from .assistant.MyAssistant import MyAssistant
from .assistant.MutiAssistant import MultiAssistant
from .excutor.PCExecutor import PCExecutor
from .excutor.K8sExecutor import K8sExecutor
from .model.openai import OpenAI
from .model.deepseek_azure import DeepSeek
from chat_history import ChatHistory

# Constants for executor and model names
EXECUTOR_PC = "pc"
EXECUTOR_K8S = "k8s"

MODEL_OPENAI = "openai"
MODEL_DEEPSEEK = "deepseek"

class AssistantCreator:
    def __init__(self, config, log: logging.Logger):
        self.config = config
        self.log = log
        self.executors = {
            "pc": PCExecutor,
            "k8s": K8sExecutor
        }
        self.models = {
            "openai": OpenAI,
            "deepseek": DeepSeek
        }

    def create_executor(self, executor_type):
        executor_class = self.executors.get(executor_type.lower())
        if not executor_class:
            raise ValueError(f"Unknown executor type: {executor_type}")
        return executor_class(self.config, self.log)
    
    def create_model(self, model_type):
        model_class = self.models.get(model_type.lower())
        if not model_class:
            raise ValueError(f"Unknown model type: {model_type}")
        return model_class(self.config, self.log)

    def setup_executor(self, assistant, executor_choice):
        # Setup the executor based on user input
        self.log.info(f"Selected executor: {executor_choice}")
        executor = self.create_executor(executor_choice)
        assistant.set_executor(executor)

    def setup_model(self, assistant, model_choice):
        self.log.info(f"Selected model: {model_choice}")
        model = self.create_model(model_choice)
        assistant.set_model(model)

    def create_assistant_with_input(self):
        # Initialize the assistant
        chat_history = ChatHistory(self.config)
        assistant = MyAssistant(chat_history, self.config, self.log)
        executor_choice = input("Select executor (1 for PCExecutor, 2 for K8sExecutor): ")
        if executor_choice == '2':
            executor_choice = 'k8s'
        else:
            executor_choice = 'pc'
        self.setup_executor(assistant, executor_choice)
        model_choice = input("Select model (1 for OpenAI, 2 for DeepSeek): ").strip().lower()
        if model_choice == '2':
            model_choice= 'deepseek'
        else:
            model_choice = 'openai'
        self.setup_model(assistant, model_choice)
        return assistant
    
    def create_manager(self):
        # Initialize the assistant
        chat_history = ChatHistory(self.config)
        assistant = MyAssistant(chat_history, self.config, self.log)
        self.setup_executor(assistant, EXECUTOR_PC)
        self.setup_model(assistant, MODEL_DEEPSEEK)
        return assistant
    
    def create_worker(self):
        # Initialize the assistant
        chat_history = ChatHistory(self.config)
        assistant = MyAssistant(chat_history, self.config, self.log)
        self.setup_executor(assistant, EXECUTOR_PC)
        self.setup_model(assistant, MODEL_OPENAI)
        return assistant
    
    def create_assistant(self, executor_choice, model_choice):
        # Initialize the assistant
        chat_history = ChatHistory(self.config)
        assistant = MyAssistant(chat_history, self.config, self.log)
        self.setup_executor(assistant, executor_choice)
        self.setup_model(assistant, model_choice)
        return assistant
    
    def create_muti_assistant(self):
        # Initialize the assistant
        chat_history = ChatHistory(self.config)
        assistant = MultiAssistant(chat_history, self.config, self.log)
        assistant.setup_manager()
        return assistant