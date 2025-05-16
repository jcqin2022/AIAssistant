from flask import Flask, request, jsonify, Response
import requests
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from mcp.server.fastmcp import FastMCP

class WhiteboardServer:
    def __init__(self, remote_server_url):
        self.app = Flask(__name__)
        self.remote_server_url = remote_server_url

    def get_history(self):
        with self.app.app_context():
            response = requests.get(f"{self.remote_server_url}/history")
            return jsonify(response.json()), response.status_code

    def clear_whiteboard(self):
        with self.app.app_context():
            response = requests.post(f"{self.remote_server_url}/clear")
            return jsonify(response.json()), response.status_code

    def draw_line(self, x, y, width, height, color):
        with self.app.app_context():
            params = {
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'color': color
            }
            response = requests.post(f"{self.remote_server_url}/draw_line", params=params)
            return jsonify(response.json()), response.status_code

    def draw_ellipse(self, x, y, rx, ry, color):
        with self.app.app_context():
            params = {
                'x': x,
                'y': y,
                'rx': rx,
                'ry': ry,
                'color': color
            }
            response = requests.post(f"{self.remote_server_url}/draw_ellipse", params=params)
            return jsonify(response.json()), response.status_code

    def draw_rect(self, x, y, width, height, color):
        with self.app.app_context():
            params = {
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'color': color
            }
            response = requests.post(f"{self.remote_server_url}/draw_rect", params=params)
            return jsonify(response.json()), response.status_code

remote_server_url = "http://localhost:8000"  # Replace with the actual remote server URL
server = WhiteboardServer(remote_server_url)
mcp = FastMCP("Math")
    # 注册工具（通过 args_schema 关联参数模型）
@mcp.tool()
def draw_line(x: float, y: float, width: float, height: float, color: str) -> int:
    """draw line with given parameters (根据给定参数绘制线条)"""
    return server.draw_line(x, y, width, height, color)

@mcp.tool()
def draw_ellipse(x: float, y: float, rx: float, ry: float, color: str) -> int:
    """draw ellipse with given parameters (根据给定参数绘制椭圆)"""
    return server.draw_ellipse(x, y, rx, ry, color)

@mcp.tool()
def draw_rect(x: float, y: float, width: float, height: float, color: str) -> int:
    """draw rect with given parameters (根据给定参数绘制矩形)"""
    return server.draw_rect(x, y, width, height, color)

@mcp.tool()
def get_history() -> tuple[Response, int]:
    """get drawing history (获取绘图历史)"""
    return server.get_history()

@mcp.tool()
def clear_whiteboard() -> tuple[Response, int]:
    """clear whiteboard (清除白板)"""
    return server.clear_whiteboard()

@mcp.prompt()
def tool_prompt() -> str:
    """Prompt for draw operations (绘制提示)"""
    return "Use tools to draw everything on target view, start point (0,0), its width is 600px, height is 800px."

# Example usage:
if __name__ == "__main__":
    # 启动服务（本地使用 stdio 传输，远程用 SSE）
    mcp.run(transport="stdio") 