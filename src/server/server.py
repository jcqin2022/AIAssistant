# math_server.py
from mcp.server.fastmcp import FastMCP  # Ensure FastMCP is correctly imported and implemented
from pydantic import BaseModel, Field

# 创建名为 "Math" 的 MCP 服务实例
mcp = FastMCP("Math")

# 注册工具（通过 args_schema 关联参数模型）
@mcp.tool()  # Ensure the tool decorator is implemented in FastMCP
def add(a: int, b: int) -> int:
    """Add two integers (加法运算)"""
    return a + b

@mcp.tool()
def multiply(x: float, y: float) -> float:
    """Multiply two numbers (乘法运算)"""
    return x * y

@mcp.prompt()
def tool_prompt() -> str:
    """Prompt for math operations (数学运算提示)"""
    return "Perform the requested math operation."

@mcp.resource("schema://tool")
def tool_resource() -> str:
    """Resource for math operations (数学运算资源)"""
    return "This is a math resource."

if __name__ == "__main__":
    # 启动服务（本地使用 stdio 传输，远程用 SSE）
    mcp.run(transport="stdio") 