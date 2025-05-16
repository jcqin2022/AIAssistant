import asyncio
from .logger import setup_logger
from src import __version__
import json
# from .client.math_client import MathClient
import logging
from .assist_creator import AssistantCreator


def run_async(assistant, question):
    # return asyncio.run(assistant.aask(question))
    return asyncio.run(assistant.aask_with_scheduler(question))

def main():
    try:
        # Load config values
        with open(r"config.json") as config_file:
            config = json.load(config_file)
        if(config is None):
            raise Exception("Config file not found")
        log = setup_logger(config)
        log.info(f"Initializing AI backend service version {__version__}")
        # client = MathClient(config, log)
        # client.run("请计算 (3 + 5) × 12 的结果")
        creator = AssistantCreator(config, log)
        # Initialize the assistant
        question_type = input("Do you have a 1: simple or a 2: complex question?: ").strip().lower()
        if question_type == "1":
            assistant = creator.create_assistant_with_input()
        else:
            assistant = creator.create_muti_assistant()
        # Start the assistant
        while True:
            user_input = input("You << ")
            if user_input.lower() == 'q':
                print("Goodbye!")
                break
            if question_type == "1":
                response = assistant.ask(user_input)
            else:
                response = run_async(assistant, user_input)
            print(f"Assistant >> {response}")
    except Exception as e:
        print(f"Exception in main(): {e}")