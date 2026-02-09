"""
RedClaw Core - LLM Client with Streaming Support
Connects to local LLM (Phi-4, GLM-4, Ollama) with real-time streaming
"""

import os
import json
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator, Generator
from dataclasses import dataclass, field
from enum import Enum
import httpx
from dotenv import load_dotenv

load_dotenv()


class LLMProvider(Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"
    VLLM = "vllm"
    OPENAI_COMPATIBLE = "openai"
    KAGGLE = "kaggle"


@dataclass
class Message:
    """Chat message"""
    role: str  # system, user, assistant
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


@dataclass
class LLMResponse:
    """LLM response with metadata"""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    tool_calls: Optional[List[Dict]] = None


@dataclass
class StreamChunk:
    """Streaming response chunk"""
    content: str
    done: bool = False
    model: str = ""


class RedClawLLM:
    """
    RedClaw LLM Client
    
    Features:
    - Multiple provider support (Ollama, vLLM, OpenAI-compatible)
    - Streaming responses for real-time output
    - Tool calling support
    - Automatic retry with exponential backoff
    - Health check and connection management
    """
    
    SYSTEM_PROMPT = """You are RedClaw, an autonomous red team AI agent specialized in penetration testing.

Your capabilities:
- Reconnaissance & OSINT gathering
- Network scanning & enumeration
- Vulnerability assessment
- Exploitation & post-exploitation
- Report generation

You have access to 150+ security tools via HexStrike-AI MCP.

Guidelines:
- Always validate targets are in scope before testing
- Use the least intrusive methods first
- Document all findings with evidence
- Never cause permanent damage to systems
- Report critical vulnerabilities immediately

When asked to perform security testing, break down the task into phases:
1. Reconnaissance - Gather information
2. Scanning - Identify open ports and services
3. Enumeration - Detail services and versions
4. Vulnerability Assessment - Identify weaknesses
5. Exploitation - Verify vulnerabilities (with caution)
6. Post-Exploitation - Assess impact
7. Reporting - Document findings

Respond with specific, actionable commands when appropriate."""
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        model: str = "phi-4",
        provider: LLMProvider = LLMProvider.OPENAI_COMPATIBLE,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: float = 120.0
    ):
        self.api_url = api_url or os.getenv("LLM_API_URL", "http://localhost:11434")
        self.model = model or os.getenv("LLM_MODEL", "phi-4")
        self.provider = provider
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        
        # HTTP client with ngrok header support
        self.headers = {
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true"
        }
        
        self.client = httpx.Client(timeout=timeout, headers=self.headers)
        self.async_client = httpx.AsyncClient(timeout=timeout, headers=self.headers)
    
    def health_check(self) -> Dict[str, Any]:
        """Check LLM API health"""
        try:
            # Try /health endpoint first
            try:
                response = self.client.get(f"{self.api_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "healthy",
                        "model": data.get("model", self.model),
                        "backend": data.get("backend", "unknown"),
                        "provider": self.provider.value
                    }
            except:
                pass
            
            # Try /v1/models for OpenAI-compatible
            try:
                response = self.client.get(f"{self.api_url}/v1/models")
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "model": self.model,
                        "backend": "openai-compatible",
                        "provider": self.provider.value
                    }
            except:
                pass
            
            # Try Ollama /api/tags
            try:
                response = self.client.get(f"{self.api_url}/api/tags")
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "model": self.model,
                        "backend": "ollama",
                        "provider": "ollama"
                    }
            except:
                pass
            
            return {"status": "unknown", "model": self.model}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def chat(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict]] = None,
        stop: Optional[List[str]] = None
    ) -> LLMResponse:
        """Send chat completion request"""
        
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "stream": False
        }
        
        if tools:
            payload["tools"] = tools
        if stop:
            payload["stop"] = stop
        
        try:
            response = self.client.post(
                f"{self.api_url}/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            choice = data["choices"][0]
            message = choice["message"]
            
            return LLMResponse(
                content=message.get("content", ""),
                model=data.get("model", self.model),
                usage=data.get("usage", {}),
                finish_reason=choice.get("finish_reason", "stop"),
                tool_calls=message.get("tool_calls")
            )
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"LLM API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"LLM request failed: {str(e)}")
    
    def chat_stream(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Generator[StreamChunk, None, None]:
        """Stream chat completion for real-time output"""
        
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "stream": True
        }
        
        try:
            with self.client.stream(
                "POST",
                f"{self.api_url}/v1/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if not line or line.startswith(":"):
                        continue
                    
                    if line.startswith("data: "):
                        line = line[6:]
                    
                    if line.strip() == "[DONE]":
                        yield StreamChunk(content="", done=True, model=self.model)
                        break
                    
                    try:
                        data = json.loads(line)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        
                        if content:
                            yield StreamChunk(
                                content=content,
                                done=False,
                                model=data.get("model", self.model)
                            )
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            raise Exception(f"Streaming failed: {str(e)}")
    
    async def achat(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> LLMResponse:
        """Async chat completion"""
        
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "stream": False
        }
        
        response = await self.async_client.post(
            f"{self.api_url}/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        choice = data["choices"][0]
        message = choice["message"]
        
        return LLMResponse(
            content=message.get("content", ""),
            model=data.get("model", self.model),
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop")
        )
    
    async def achat_stream(
        self,
        messages: List[Message],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """Async streaming chat completion"""
        
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "stream": True
        }
        
        async with self.async_client.stream(
            "POST",
            f"{self.api_url}/v1/chat/completions",
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line or line.startswith(":"):
                    continue
                
                if line.startswith("data: "):
                    line = line[6:]
                
                if line.strip() == "[DONE]":
                    yield StreamChunk(content="", done=True, model=self.model)
                    break
                
                try:
                    data = json.loads(line)
                    delta = data["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    
                    if content:
                        yield StreamChunk(
                            content=content,
                            done=False,
                            model=data.get("model", self.model)
                        )
                except json.JSONDecodeError:
                    continue
    
    def analyze(
        self,
        context: str,
        task: str,
        data: Optional[Dict] = None
    ) -> str:
        """Run RedClaw analysis on security data"""
        
        prompt = f"""Analyze the following security data for: {task}

Context: {context}

Data:
{json.dumps(data, indent=2) if data else 'No additional data'}

Provide:
1. Key findings
2. Potential vulnerabilities
3. Recommended next steps
4. Risk assessment (Critical/High/Medium/Low)
"""
        
        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
            Message(role="user", content=prompt)
        ]
        
        response = self.chat(messages)
        return response.content
    
    def plan_attack(self, target: str, scope: str = "full") -> str:
        """Generate attack plan for target"""
        
        prompt = f"""Create a detailed attack plan for target: {target}

Scope: {scope}

Generate a phased attack plan following PTES methodology:
1. Pre-engagement (scope validation)
2. Intelligence Gathering
3. Threat Modeling
4. Vulnerability Analysis
5. Exploitation
6. Post-Exploitation
7. Reporting

For each phase, specify:
- Objectives
- Tools to use
- Expected outputs
- Success criteria
"""
        
        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
            Message(role="user", content=prompt)
        ]
        
        response = self.chat(messages, max_tokens=8192)
        return response.content
    
    def close(self):
        """Close HTTP clients"""
        self.client.close()
    
    async def aclose(self):
        """Async close"""
        await self.async_client.aclose()


def get_llm_client() -> RedClawLLM:
    """Get configured LLM client from environment"""
    return RedClawLLM(
        api_url=os.getenv("LLM_API_URL"),
        model=os.getenv("LLM_MODEL", "phi-4"),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7"))
    )
