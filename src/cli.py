from .MyAssistant import MyAssistant
from .PCExecutor import PCExecutor
from .K8sExecutor import K8sExecutor
from chat_history import ChatHistory
from .logger import setup_logger
from src import __version__
import json

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
        executor_choice = input("Select executor (1 for PCExecutor, 2 for K8sExecutor): ")
        if executor_choice == '1':
            executor = PCExecutor(config, log)
        elif executor_choice == '2':
            executor = K8sExecutor(config, log)
        else:
            print("Invalid choice, defaulting to PCExecutor.")
            executor = PCExecutor()
        assistant.set_executor(executor)
        while True:
            user_input = input("You << ")
            if user_input.lower() == 'q':
                print("Goodbye!")
                break
            response = assistant.ask(user_input)
            print(f"Assistant >> {response}")
    except Exception as e:
        print(f"Exception in main(): {e}")