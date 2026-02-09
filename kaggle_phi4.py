"""
RedClaw Phi-4 API Server for Kaggle (using llama.cpp)
=====================================================
Uses llama-cpp-python with pre-built CUDA wheel for fast setup.

Instructions:
1. Create new Kaggle notebook with GPU T4 x2
2. Enable Internet access
3. Copy each CELL section and run sequentially
"""

# ============================================
# CELL 1: Install llama-cpp-python (Pre-built wheel)
# ============================================
# Pre-built wheel - much faster than source build
!pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122 --no-cache-dir
!pip install -q fastapi uvicorn pyngrok nest-asyncio

# ============================================
# CELL 2: Download Phi-4 GGUF Model
# ============================================
import os

print("Downloading Phi-4 GGUF model (~8.4GB)...")
os.makedirs("/kaggle/working/models", exist_ok=True)

# Direct download with wget - more reliable
!wget -q --show-progress -O /kaggle/working/models/phi-4-Q4_K_S.gguf \
    "https://huggingface.co/bartowski/phi-4-GGUF/resolve/main/phi-4-Q4_K_S.gguf"

MODEL_PATH = "/kaggle/working/models/phi-4-Q4_K_S.gguf"
print(f"✅ Model downloaded to: {MODEL_PATH}")

# ============================================
# CELL 3: Load Model with llama-cpp-python
# ============================================
from llama_cpp import Llama

print("Loading Phi-4 model into GPU...")

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=8192,          # Context window
    n_gpu_layers=-1,     # All layers on GPU
    n_threads=4,
    verbose=True
)

print("✅ Model loaded successfully!")

# ============================================
# CELL 4: Setup FastAPI Server
# ============================================
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid

app = FastAPI(
    title="RedClaw Phi-4 API",
    description="Phi-4 GGUF API Server for RedClaw",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    max_tokens: Optional[int] = 2048
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    stream: Optional[bool] = False

# ============================================
# CELL 5: API Endpoints
# ============================================
@app.get("/")
async def root():
    return {"status": "online", "model": "phi-4-Q4_K_S"}

@app.get("/health")
async def health():
    return {"status": "healthy", "model": "phi-4", "device": "cuda"}

@app.get("/v1/models")
async def list_models():
    return {"data": [{"id": "phi-4", "object": "model"}]}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        response = llm.create_chat_completion(
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=max(request.temperature, 0.01),
            top_p=request.top_p,
        )
        
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "model": "phi-4",
            "choices": response["choices"],
            "usage": response["usage"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# CELL 6: RedClaw PenTest Endpoint
# ============================================
class PenTestRequest(BaseModel):
    target: str
    task_type: str
    context: Optional[str] = None
    previous_findings: Optional[List[str]] = []

@app.post("/v1/pentest/analyze")
async def pentest_analyze(request: PenTestRequest):
    system_prompt = """You are RedClaw, an elite autonomous penetration testing AI.
Analyze security findings and provide precise, actionable exploitation steps.
Follow MITRE ATT&CK framework. Output specific commands."""
    
    user_prompt = f"""Target: {request.target}
Task: {request.task_type}
Context: {request.context or 'Initial'}
Findings: {', '.join(request.previous_findings) if request.previous_findings else 'None'}

Provide tactical steps with commands."""

    try:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2048,
            temperature=0.3,
        )
        
        return {
            "status": "success",
            "analysis": response["choices"][0]["message"]["content"],
            "task_type": request.task_type,
            "target": request.target
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# CELL 7: Start Server with ngrok
# ============================================
import nest_asyncio
from pyngrok import ngrok
import uvicorn
import threading
import time

nest_asyncio.apply()

# Your ngrok authtoken
NGROK_AUTH_TOKEN = "32NEHC8IvRXfkU1MIWo6LtrOVOb_2LRzh77NZVQFcGupWdRsm"
ngrok.set_auth_token(NGROK_AUTH_TOKEN)

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(3)

public_url = ngrok.connect(8000)
print("\n" + "="*60)
print("🚀 RedClaw Phi-4 API Server is LIVE!")
print("="*60)
print(f"\n📡 Public URL: {public_url}")
print(f"\n🔗 Endpoints:")
print(f"   - Health: {public_url}/health")
print(f"   - Chat: {public_url}/v1/chat/completions")
print(f"   - PenTest: {public_url}/v1/pentest/analyze")
print(f"\n⚙️ RedClaw Config:")
print(f'   LLM_API_URL="{public_url}"')
print("="*60)

print("\n⏳ Server running... Keep notebook open!")
while True:
    time.sleep(60)
    print(".", end="", flush=True)
