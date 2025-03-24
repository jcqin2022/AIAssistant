from .MyAssistant import MyAssistant
from .excutor.PCExecutor import PCExecutor
from .excutor.K8sExecutor import K8sExecutor
from chat_history import ChatHistory
from .logger import setup_logger
from src import __version__
import json
from .model.openai import OpenAI
from .model.deepseek_azure import DeepSeek
from .model.base_model import BaseModel
import logging

def setup_executor(assistant: MyAssistant, config: dict, log: logging.Logger):
    executor_choice = input("Select executor (1 for PCExecutor, 2 for K8sExecutor): ")
    if executor_choice == '2':
        executor = K8sExecutor(config, log)
    else:
        print("Default to PCExecutor.")
        executor = PCExecutor(config, log)
    assistant.set_executor(executor)
    
def setup_model(assistant: MyAssistant, config: dict, log: logging.Logger):
    model_choice = input("Select model (1 openai for OpenAI, 2 for DeepSeek): ").strip().lower()
    if model_choice == '2':
        model = DeepSeek(config, log)
    else:
        print("default to OpenAI.")
        model = OpenAI(config, log)
    assistant.set_model(model)

def main():
    try:
        # Load config values
        with open(r"config.json") as config_file:
            config = json.load(config_file)
        if(config is None):
            raise Exception("Config file not found")
        log = setup_logger(config)
        log.info(f"Initializing AI backend service version {__version__}")
        chat_history = ChatHistory(config)
        assistant = MyAssistant(chat_history, config, log)
        setup_executor(assistant, config, log)
        setup_model(assistant, config, log)
        while True:
            user_input = input("You << ")
            if user_input.lower() == 'q':
                print("Goodbye!")
                break
            response = assistant.ask(user_input)
            print(f"Assistant >> {response}")
    except Exception as e:
        print(f"Exception in main(): {e}")