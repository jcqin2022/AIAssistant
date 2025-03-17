from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
import os
from azure.core.credentials import AzureKeyCredential

# 示例1：数据查询函数
def get_user_profile(user_id: str) -> dict:
    """根据用户ID获取本地存储的档案信息"""
    # 模拟本地数据库查询
    profiles = {
        "001": {"name": "张三", "age": 28, "vip_level": 2},
        "002": {"name": "李四", "age": 35, "vip_level": 5}
    }
    return profiles.get(user_id, {})

# 示例2：计算函数
def calculate_expression(expression: str) -> float:
    """执行数学表达式计算（安全版本）"""
    allowed_chars = set("0123456789+-*/.() ")
    if not all(c in allowed_chars for c in expression):
        raise ValueError("包含非法字符")
    return eval(expression)

def ask(config):
    try:
        credential = AzureKeyCredential(config["AZURE_DS_KEY"])
        # 创建Agent
        llm = ChatDeepSeek(
            api_base=config["AZURE_DS_ENDPOINT"],
            api_key=credential,
            model=config["AZURE_DS_NAME"],
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

        # 定义工具集
        tools = [
            Tool(
                name="UserProfile",
                func=get_user_profile,
                description="根据用户ID查询档案信息，输入应为用户ID字符串"
            ),
            Tool(
                name="Calculator",
                func=calculate_expression,
                description="执行数学表达式计算，输入示例：'(12.5 + 4)*2'"
            )
        ]

        prompt = ChatPromptTemplate.from_template("""
        你是一个智能助手，可以访问本地函数工具。请根据用户需求选择合适工具。

        可用工具：
        {tools}

        用户输入：
        {input}
        Thought:
        {agent_scratchpad}
        Tools Name:
        {tool_names}

        请按此格式响应：
        Thought: 分析需求并选择工具
        Action: 工具名称
        Action Input: 工具需要的输入
        """)

        agent = create_react_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        result = agent_executor.invoke({"input": "hello"})
        print(f"\nAI响应：{result['output']}")
    except Exception as e:
            print(f"执行出错：{str(e)}")
        
        