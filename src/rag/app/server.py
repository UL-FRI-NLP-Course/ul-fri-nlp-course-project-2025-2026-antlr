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
    temperature: float
    use_context: bool


# -----------------------------
# Chat endpoint
# -----------------------------


@app.post("/v1/chat/completions")
def chat_completion(req: ChatCompletionRequest):
    # 1. Isolate chat history and latest message
    history_messages = req.messages[:-1]
    question = req.messages[-1].content

    # 2. Convert active dialogue into a formatted tracker string
    history_str = ""
    if len(history_messages) > 0:
        # Keep only the last 4 exchanges to stay clear of token boundaries
        history_str = "\n".join([f"{m.role.upper()}: {m.content}" for m in history_messages[-4:]])

    # 3. Handle Context Query Rewriting
    if history_str and req.use_context:
        print(f"[debug-memory] Pre-rewriting lookup: '{question}'")
        search_query = Synthesizer.rewrite_query(history_str=history_str, latest_question=question)
        print(f"[debug-memory] Rewritten standalone query: '{search_query}'")
    else:
        search_query = question

    # 4. Perform Retrieval on database using search_query
    results = vec.search(search_query, limit=3)

    # 5. Extract configuration and evaluate generation path
    temperature = float(req.temperature)
    use_context = True  # default is True
    if req.use_context is not None:
        use_context = bool(req.use_context)
    
    print("[debug] temperature is %.2f" % temperature)
    
    # Send both the immediate question and the historical footprint forward
    response = Synthesizer.generate_response(
        question=question,
        context=results,
        history_str=history_str,
        temperature=temperature,
        use_context=use_context
    )

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