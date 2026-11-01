"""Web API for the AIOU FAQ chatbot.

Run:  uvicorn app:app --reload --port 8000
Test: curl -X POST localhost:8000/chat -H "Content-Type: application/json" \
        -d '{"message": "how do I submit my assignment?"}'
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from chatbot import FAQBot

app = FastAPI(title="AIOU Student FAQ Bot")

# In production, replace "*" with your website's origin, e.g. ["https://yourschool.example"]
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

bot = FAQBot()


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=1000)


@app.post("/chat")
def chat(req: ChatRequest):
    return bot.reply(req.message)


@app.get("/health")
def health():
    return {"status": "ok", "entries": len(bot.kb)}


@app.get("/")
def demo_page():
    return FileResponse(Path(__file__).with_name("index.html"))
