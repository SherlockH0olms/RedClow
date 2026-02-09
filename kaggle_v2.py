# =====================================================
# REDCLAW GLM-4 API - FIXED VERSION
# GLM-4 uses special tokenizer methods
# =====================================================

# CELL 1: Install
!pip install -q transformers accelerate torch fastapi uvicorn pyngrok nest-asyncio

# CELL 2: Setup and Load Model
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn, nest_asyncio, threading, time
from pyngrok import ngrok

MODEL_ID = "THUDM/GLM-4-9B-Chat"
NGROK_TOKEN = "32NEHC8IvRXfkU1MIWo6LtrOVOb_2LRzh77NZVQFcGupWdRsm"
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True)
print("Model loaded!")

# CELL 3: FastAPI with GLM-4 specific tokenization
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    max_tokens: Optional[int] = 512

@app.get("/health")
async def health():
    return {"status": "ok", "device": device}

@app.post("/v1/chat/completions")
async def chat(request: ChatRequest):
    try:
        # Convert to list of dicts for GLM-4
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        # GLM-4 has a special method for chat - try it first
        if hasattr(tokenizer, 'build_chat_input'):
            # Use GLM-4's native chat input builder
            inputs = tokenizer.build_chat_input(messages[-1]["content"], history=[], role="user")
            inputs = {k: v.to(device) for k, v in inputs.items()}
            input_len = inputs['input_ids'].shape[1]
        elif hasattr(tokenizer, 'apply_chat_template'):
            # Try apply_chat_template with tokenization
            input_ids = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt")
            if input_ids is not None:
                inputs = {"input_ids": input_ids.to(device)}
                input_len = input_ids.shape[1]
            else:
                raise ValueError("apply_chat_template returned None")
        else:
            # Fallback: manual prompt
            prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages]) + "\nassistant:"
            encoded = tokenizer.encode(prompt, return_tensors="pt")
            inputs = {"input_ids": encoded.to(device)}
            input_len = encoded.shape[1]
        
        # Generate
        outputs = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens or 512,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
        response = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True).strip()
        
        return {
            "id": "chat-1",
            "model": MODEL_ID,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": response}}],
            "usage": {"prompt_tokens": input_len, "completion_tokens": len(outputs[0]) - input_len}
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

# CELL 4: Start server
nest_asyncio.apply()
ngrok.set_auth_token(NGROK_TOKEN)

def run():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

threading.Thread(target=run, daemon=True).start()
time.sleep(3)
url = ngrok.connect(8000)
print(f"\n{'='*50}\n🚀 API LIVE: {url}\n{'='*50}")

while True:
    time.sleep(60)
