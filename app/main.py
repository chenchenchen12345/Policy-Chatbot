import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from app.rag import build_chatbot

from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="RAG Chatbot (FastAPI + Memory)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; refine for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chatbot = build_chatbot()

@app.get("/")
def read_root():
    return {"status": "online", "message": "Richmond Policy Chatbot API is running. Visit /docs for documentation."}

@app.get("/health")
def health():
    return {"status": "ok", "project": "richmond_policy_chat"}

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    """
    session_id controls memory.
    Reuse the same session_id to continue a conversation with full history.
    """
    # Agents return a dict, we need the 'output' string
    result = chatbot.invoke(
        {"input": req.message},
        config={"configurable": {"session_id": req.session_id}},
    )
    
    # Extract just the text from the agent response
    raw_answer = result.get("output", str(result))
    
    # If Claude returns a list of blocks, extract the text
    if isinstance(raw_answer, list):
        answer = " ".join([block.get("text", "") for block in raw_answer if block.get("type") == "text"])
    else:
        answer = str(raw_answer)

    return {"answer": answer}
