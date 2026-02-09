"""
RedClaw LLM Manager
Multi-backend LLM management with fallback, streaming, and context window control
"""

import os
import json
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator, Callable
from dataclasses import dataclass
import httpx

from .config import (
    LLMConfig, LLMBackend, BACKEND_PRESETS, 
    get_config, configure_backend
)
from .llm_client import RedClawLLM, Message, LLMResponse, StreamChunk


class LLMManager:
    """
    Multi-backend LLM manager with:
    - Automatic fallback chain
    - Context window management
    - Streaming support
    - Health monitoring
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or get_config().llm
        self.clients: Dict[LLMBackend, RedClawLLM] = {}
        self.active_backend: Optional[LLMBackend] = None
        self.health_status: Dict[LLMBackend, bool] = {}
        
        # Initialize primary client
        self._init_client(self.config.backend)
    
    def _init_client(self, backend: LLMBackend) -> Optional[RedClawLLM]:
        """Initialize LLM client for backend"""
        if backend in self.clients:
            return self.clients[backend]
        
        preset = BACKEND_PRESETS.get(backend, {})
        
        # Determine API URL
        api_url = self.config.api_url
        if backend == LLMBackend.KAGGLE_PHI4:
            api_url = os.getenv("KAGGLE_API_URL", preset.get("api_url", ""))
        elif backend == LLMBackend.OLLAMA:
            api_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        elif backend == LLMBackend.VLLM:
            api_url = os.getenv("VLLM_URL", "http://localhost:8000")
        
        try:
            client = RedClawLLM(
                api_url=api_url,
                model=self.config.model or preset.get("model", "phi-4"),
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.timeout
            )
            self.clients[backend] = client
            return client
        except Exception as e:
            print(f"[LLMManager] Failed to init {backend.value}: {e}")
            return None
    
    def _get_active_client(self) -> RedClawLLM:
        """Get active LLM client with fallback"""
        # Try primary backend
        if self.active_backend and self.active_backend in self.clients:
            if self.health_status.get(self.active_backend, True):
                return self.clients[self.active_backend]
        
        # Try primary config backend
        client = self._init_client(self.config.backend)
        if client and self._check_health(self.config.backend):
            self.active_backend = self.config.backend
            return client
        
        # Fallback chain
        for fallback in self.config.fallback_backends:
            client = self._init_client(fallback)
            if client and self._check_health(fallback):
                self.active_backend = fallback
                print(f"[LLMManager] Falling back to {fallback.value}")
                return client
        
        raise RuntimeError("No LLM backend available")
    
    def _check_health(self, backend: LLMBackend) -> bool:
        """Check backend health"""
        if backend not in self.clients:
            return False
        
        try:
            status = self.clients[backend].health_check()
            healthy = status.get("status") in ["healthy", "unknown"]
            self.health_status[backend] = healthy
            return healthy
        except Exception:
            self.health_status[backend] = False
            return False
    
    def _truncate_context(
        self, 
        messages: List[Message],
        max_tokens: Optional[int] = None
    ) -> List[Message]:
        """Truncate messages to fit context window"""
        max_ctx = max_tokens or self.config.context_window
        
        # Estimate tokens (rough: 4 chars per token)
        def estimate_tokens(msg: Message) -> int:
            return len(msg.content) // 4 + 10
        
        total = sum(estimate_tokens(m) for m in messages)
        
        if total <= max_ctx:
            return messages
        
        # Keep system message and last N messages
        result = []
        running_total = 0
        
        # Always keep system message
        for msg in messages:
            if msg.role == "system":
                result.append(msg)
                running_total += estimate_tokens(msg)
                break
        
        # Add messages from end until we hit limit
        remaining = max_ctx - running_total - self.config.max_tokens
        reversed_msgs = list(reversed([m for m in messages if m.role != "system"]))
        kept_msgs = []
        
        for msg in reversed_msgs:
            tokens = estimate_tokens(msg)
            if running_total + tokens < remaining:
                kept_msgs.append(msg)
                running_total += tokens
            else:
                break
        
        result.extend(reversed(kept_msgs))
        return result
    
    def chat(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict]] = None
    ) -> LLMResponse:
        """Chat completion with context management"""
        client = self._get_active_client()
        truncated = self._truncate_context(messages, max_tokens)
        
        return client.chat(
            messages=truncated,
            max_tokens=max_tokens or self.config.max_tokens,
            temperature=temperature or self.config.temperature,
            tools=tools
        )
    
    async def achat(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> LLMResponse:
        """Async chat completion"""
        client = self._get_active_client()
        truncated = self._truncate_context(messages, max_tokens)
        
        return await client.achat(
            messages=truncated,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def stream(
        self,
        messages: List[Message],
        callback: Optional[Callable[[str], None]] = None
    ):
        """Stream chat with optional callback"""
        client = self._get_active_client()
        truncated = self._truncate_context(messages)
        
        full_response = ""
        for chunk in client.chat_stream(truncated):
            if chunk.content:
                full_response += chunk.content
                if callback:
                    callback(chunk.content)
            if chunk.done:
                break
        
        return full_response
    
    async def astream(
        self,
        messages: List[Message],
        callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """Async stream chat"""
        client = self._get_active_client()
        truncated = self._truncate_context(messages)
        
        full_response = ""
        async for chunk in client.achat_stream(truncated):
            if chunk.content:
                full_response += chunk.content
                if callback:
                    callback(chunk.content)
            if chunk.done:
                break
        
        return full_response
    
    def get_status(self) -> Dict[str, Any]:
        """Get manager status"""
        return {
            "active_backend": self.active_backend.value if self.active_backend else None,
            "config_backend": self.config.backend.value,
            "model": self.config.model,
            "context_window": self.config.context_window,
            "health": {
                k.value: v for k, v in self.health_status.items()
            },
            "available_backends": [b.value for b in self.clients.keys()]
        }
    
    def switch_backend(self, backend: LLMBackend) -> bool:
        """Manually switch backend"""
        client = self._init_client(backend)
        if client and self._check_health(backend):
            self.active_backend = backend
            return True
        return False
    
    def close(self):
        """Close all clients"""
        for client in self.clients.values():
            try:
                client.close()
            except:
                pass


# Singleton manager
_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """Get global LLM manager"""
    global _manager
    if _manager is None:
        _manager = LLMManager()
    return _manager


def configure_llm(
    backend: str = "ollama",
    api_url: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> LLMManager:
    """Configure and return LLM manager"""
    global _manager
    
    backend_map = {
        "kaggle": LLMBackend.KAGGLE_PHI4,
        "ollama": LLMBackend.OLLAMA,
        "vllm": LLMBackend.VLLM,
        "openai": LLMBackend.OPENAI,
        "local": LLMBackend.LOCAL,
    }
    
    backend_enum = backend_map.get(backend.lower(), LLMBackend.OLLAMA)
    config = configure_backend(backend_enum, api_url=api_url, model=model, **kwargs)
    
    _manager = LLMManager(config)
    return _manager
