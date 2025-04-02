# math_server.py
from mcp.server.fastmcp import FastMCP  # Ensure FastMCP is correctly imported and implemented
from pydantic import BaseModel, Field

# 创建名为 "Math" 的 MCP 服务实例
mcp = FastMCP("Math")

# 定义工具参数模型（必须继承 BaseModel）
class AddArgs(BaseModel):
    a: int = Field(..., description="First number")
    b: int = Field(..., description="Second number")

class MultiplyArgs(BaseModel):
    x: float = Field(..., description="Multiplicand")
    y: float = Field(..., description="Multiplier")

# 注册工具（通过 args_schema 关联参数模型）
@mcp.tool()  # Ensure the tool decorator is implemented in FastMCP
def add(a: int, b: int) -> int:
    """Add two integers (加法运算)"""
    return a + b

@mcp.tool()
def multiply(x: float, y: float) -> float:
    """Multiply two numbers (乘法运算)"""
    return x * y

if __name__ == "__main__":
    # 启动服务（本地使用 stdio 传输，远程用 SSE）
    mcp.run(transport="stdio") 