"""
RedClaw - LLM Client for Kaggle Phi-4 API
Connects to the Phi-4 GGUF model running on Kaggle via ngrok tunnel.
"""

import os
import json
import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Message:
    role: str  # "system", "user", "assistant"
    content: str

@dataclass 
class LLMResponse:
    content: str
    model: str
    tokens_used: int
    finish_reason: str

class RedClawLLM:
    """LLM Client for RedClaw - connects to Kaggle Phi-4 API"""
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        model: str = "phi-4",
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        self.api_url = api_url or os.getenv("LLM_API_URL", "https://f5cd-34-44-51-201.ngrok-free.app")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Headers for ngrok tunnel
        self.headers = {
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true"
        }
        
        self.client = httpx.Client(timeout=120.0, headers=self.headers)
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy"""
        try:
            response = self.client.get(f"{self.api_url}/health")
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def chat(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop: Optional[List[str]] = None
    ) -> LLMResponse:
        """
        Send a chat completion request to the Phi-4 API
        
        Args:
            messages: List of Message objects with role and content
            max_tokens: Override default max tokens
            temperature: Override default temperature
            stop: Stop sequences
            
        Returns:
            LLMResponse with generated content
        """
        payload = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
        }
        
        if stop:
            payload["stop"] = stop
        
        response = self.client.post(
            f"{self.api_url}/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        choice = data["choices"][0]
        
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.model),
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop")
        )
    
    def analyze_pentest(
        self,
        context: str,
        tool_output: Optional[str] = None,
        phase: str = "reconnaissance"
    ) -> Dict[str, Any]:
        """
        RedClaw-specific endpoint for penetration testing analysis
        
        Args:
            context: Current context and task description
            tool_output: Output from security tools to analyze  
            phase: Current phase (reconnaissance, scanning, exploitation, post-exploitation)
            
        Returns:
            Analysis with recommended actions
        """
        payload = {
            "context": context,
            "tool_output": tool_output or "",
            "phase": phase
        }
        
        response = self.client.post(
            f"{self.api_url}/v1/pentest/analyze",
            json=payload
        )
        response.raise_for_status()
        
        return response.json()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()


# Convenience function for quick usage
def get_llm_client() -> RedClawLLM:
    """Get a configured LLM client instance"""
    return RedClawLLM(
        api_url=os.getenv("LLM_API_URL"),
        model=os.getenv("LLM_MODEL", "phi-4"),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7"))
    )


if __name__ == "__main__":
    # Quick test
    client = get_llm_client()
    
    print("🔍 Testing RedClaw LLM Client...")
    print(f"   API URL: {client.api_url}")
    
    # Health check
    health = client.health_check()
    print(f"   Health: {health}")
    
    if health.get("status") == "healthy":
        # Test chat
        messages = [
            Message(role="system", content="You are a penetration testing assistant."),
            Message(role="user", content="What is the first step in reconnaissance?")
        ]
        
        response = client.chat(messages, max_tokens=200)
        print(f"\n📝 Response:\n{response.content}")
        print(f"\n   Tokens used: {response.tokens_used}")
