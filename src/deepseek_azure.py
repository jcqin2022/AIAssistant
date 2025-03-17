# Install the following dependencies: azure.identity and azure-ai-inference
import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

def ask2(config):
    endpoint = config["AZURE_DS_ENDPOINT"]
    model_name = config["AZURE_DS_NAME"]
    key = config["AZURE_DS_KEY"]
    client = ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    response = client.complete(
    messages=[
        SystemMessage(content="You are a helpful assistant."),
        UserMessage(content="What are 3 things to visit in Seattle?")
    ],
    model = model_name,
    max_tokens=1000
    )

    print(response)