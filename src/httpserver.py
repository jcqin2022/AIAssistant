from fastapi import FastAPI
import uvicorn
from .aiservice import AiService
import logging

class HttpServer:
    def __init__(self, ai_service: AiService, log: logging.Logger):
        self.log = log
        self.app = FastAPI()
        self.setup_routes()
        self.service = ai_service

    def setup_routes(self):
        @self.app.get("/GetVersion")
        async def get_version():
            return {"version": "1.0.0"}

        @self.app.get("/Ask")
        async def ask(question: str):
            # Implement your logic to handle the question here
            answer=await self.service.ask(question)
            return {"question": question, "answer": answer}

    def run(self, host="0.0.0.0", port=8000):
        uvicorn.run(
            self.app, 
            host=host, 
            port=port, 
            workers=1, 
            loop="asyncio", 
            http="auto", 
            timeout_keep_alive=30
            )

