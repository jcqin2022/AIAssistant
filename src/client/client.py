import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import os
import logging
from logging.handlers import RotatingFileHandler
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.tools import Tool


class Client:
    def __init__(self, config: dict, log: logging.Logger):
        self.config = config
        self.log = log
        self.model = None
        self.server_script_path=os.getcwd() + "\\demo\\draw_server.py"
        self.server_params = StdioServerParameters(
            command="python", # winddows, python, but for linux, use python3
            # command="python3", # for linux
            args=[self.server_script_path]
        )
        self.setup_model()

    def setup_model(self):
        try:
            self.model = AzureChatOpenAI(
                model_name=self.config["MODEL_NAME"],
                azure_endpoint=self.config["AZURE_OPENAI_ENDPOINT"], 
                openai_api_key=self.config["AZURE_OPENAI_KEY"],
                openai_api_version=self.config["OPENAI_API_VERSION"],
            )
        except Exception as e:
            self.log.error(f"Error setting up model: {e}")
            return None

    async def calculate(self, query):
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    try:
                        await session.initialize()  # 初始化连接
                        prompts = await session.list_prompts()
                        prompt = await session.get_prompt("tool_prompt")  # 获取提示
                        resources = await session.list_resources()
                        # resource = await session.read_resource("schema://tool")  # 获取资源
                        tools = await load_mcp_tools(session)  # 加载服务端工具
                        
                        # 调用工具并返回结果
                        serializable_tools = [
                            {
                                "type": "function",
                                "function": {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "parameters": tool.args_schema # 提取参数结构
                                }
                            }
                            for tool in tools
                        ]
                        messages = [
                            SystemMessage(content=prompt.messages[0].content.text),
                            HumanMessage(content=query)
                        ]
                        self.log.info(f"messages: {messages}")
                        tool_names = [tool["function"]["name"] for tool in serializable_tools]
                        self.log.info(f"Tool names in server: {tool_names}")
                        finish = ""
                        while finish!= "stop":
                            response = await self.model.agenerate([messages], tools=serializable_tools)
                            ai_message = response.generations[0][0].message
                            messages.append(ai_message)
                            finish = response.generations[0][0].generation_info["finish_reason"]
                            # 检查是否有工具调用请求
                            if hasattr(ai_message, 'tool_calls') and ai_message.tool_calls:
                                for tool_call in ai_message.tool_calls:
                                    tool_name = tool_call['name']
                                    args = tool_call['args']
                                    
                                    # 执行工具调用
                                    tool_result = await self._execute_tool(session, tool_name, args)
                                    
                                    # 将结果追加到消息历史
                                    messages.append(ToolMessage(
                                        content=tool_result,
                                        tool_call_id=tool_call['id']
                                    ))
                        # 第二次调用模型生成最终回答
                        self.log.debug(f"messages: {messages}")
                        self.log.info(f"final_response: {response.generations[0][0].text}")
                        return response.generations[0][0].text
                    except Exception as e:
                        self.log.error(f"Error invoking model: {e}")
                        return None
    
    async def _execute_tool(self, session: ClientSession, tool_name: str, args: dict) -> str:
        """调用 MCP Server 执行工具"""
        try:
            result = await session.call_tool(tool_name, args)  # 关键：通过 MCP 会话调用工具
            text = result.content[0].text if isinstance(result.content, list) else result.content
            self.log.info(f"function name: {tool_name} - args: {args} - result: {text}")
            return result
        except Exception as e:
            return  self.log.error(f"Tool Error: {e}")
    
    def run(self, message):
        try:
            self.log.info(f"Query: {message}")
            result = asyncio.run(self.calculate(message))
            self.log.info(f"Result: {result}")
            return result
        except Exception as e:
            self.log.error(f"Error running: {e}")
            return None
        
def setup_logger(config:dict):
        verbose = config.get("VERBOSE", False)
        log_file = config.get("LOG_FILE", "ai_service.log")
        log_format = f"%(asctime)s [0.1] [%(levelname)s] %(filename)s:%(lineno)d: %(message)s"
        date_format = "[%Y-%m-%d %H:%M:%S]"
        formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
        logging.basicConfig(
            format=log_format,
            datefmt=date_format,
        )
        if os.path.exists(log_file):
            os.remove(log_file)
        handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=1, encoding="utf-8"
        )
        handler.stream.flush()
        handler.setFormatter(formatter)
        log = logging.getLogger("ai_service")
        log.addHandler(handler)
        log.setLevel(logging.DEBUG if verbose else logging.INFO)
        return log

if __name__ == "__main__":
    async def main():
        print(f"Current folder path: {os.getcwd()}")
        # Load config values
        with open(r"config.json") as config_file:
            config = json.load(config_file)
        if(config is None):
            raise Exception("Config file not found")
        log = setup_logger(config)
        log.info(f"Initializing AI backend service version 0.1")
        client = Client(config, log)
        # result = await client.calculate("请计算 (3 + 5) × 12 的结果")
        # result = await client.calculate("清理下画布，然后在中心画几个图形，包括直线，圆，矩形等")
        result = await client.calculate("清理下画布，然后在画布上画一只简单的蓝色小狗，多一点细节")
    asyncio.run(main())