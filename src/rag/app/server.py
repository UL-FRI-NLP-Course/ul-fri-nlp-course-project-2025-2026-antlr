import argparse
from typing import List

import uvicorn
from database.vector_store import VectorStore
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from services.synthesizer import Synthesizer

app = FastAPI()

vec = VectorStore()

# -----------------------------
# OpenAI-compatible schemas
# -----------------------------


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]


# -----------------------------
# Chat endpoint
# -----------------------------


@app.post("/v1/chat/completions")
def chat_completion(req: ChatCompletionRequest):
    # last user message
    question = req.messages[-1].content

    # retrieval
    results = vec.search(question, limit=3)

    # synthesis
    response = Synthesizer.generate_response(question=question, context=results)

    answer = response[0]["generated_text"][-1]["content"]

    return {
        "id": "chatcmpl-local",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": answer,
                },
                "finish_reason": "stop",
            }
        ],
    }


app.mount("/", StaticFiles(directory="src/page", html=True), name="static")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", type=str, default="0.0.0.0")

    args = parser.parse_args()

    print(f"Running server on {args.host}:{args.port}")

    uvicorn.run("server:app", host=args.host, port=args.port, reload=False)
