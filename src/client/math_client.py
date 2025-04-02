import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
import asyncio
import logging
from langchain.tools import Tool


class MathClient:
    def __init__(self, config: dict, log: logging.Logger):
        self.config = config
        self.log = log
        self.model = None
        self.server_script_path="/home/alic/data/AIAssistant/src/server/math_server.py"
        self.server_params = StdioServerParameters(
            command="python3",
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
            # self.model = AzureChatOpenAI(
            #     model_name=self.config["AZURE_DS_NAME"],
            #     azure_endpoint=self.config["AZURE_DS_ENDPOINT"], 
            #     openai_api_key=self.config["AZURE_DS_KEY"],
            #     openai_api_version=self.config["DS_API_VERSION"],
            # )
        except Exception as e:
            self.log.error(f"Error setting up model: {e}")
            return None

    async def calculate(self, query):
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    try:
                        await session.initialize()  # 初始化连接
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
                            SystemMessage(content="Use tools and return final answer."),
                            HumanMessage(content=query)
                        ]
                        response = await self.model.agenerate([messages], tools=serializable_tools)
                        self.log.info(f"Response: {response}")
                        ai_message = response.generations[0][0].message
                        messages.append(ai_message)
                        
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
                            final_response = await self.model.agenerate([messages], tools=serializable_tools)
                            return final_response.generations[0][0].text
                        else:
                            return ai_message.content
                    except Exception as e:
                        self.log.error(f"Error invoking model: {e}")
                        return None
    
    async def _execute_tool(self, session: ClientSession, tool_name: str, args: dict) -> str:
        """调用 MCP Server 执行工具"""
        try:
            result = await session.call_tool(tool_name, args)  # 关键：通过 MCP 会话调用工具
            return str(result)
        except Exception as e:
            return f"Tool Error: {e}"
    
    def run(self, message):
        try:
            self.log.info(f"Query: {message}")
            result = asyncio.run(self.calculate(message))
            self.log.info(f"Result: {result}")
            return result
        except Exception as e:
            self.log.error(f"Error running: {e}")
            return None

if __name__ == "__main__":
    async def main():
        client = MathClient()
        result = await client.calculate("请计算 (3 + 5) × 12 的结果")
        print(result)

    asyncio.run(main())