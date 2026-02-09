"""
RedClaw Configuration Module
Centralized configuration for LLM backends, tools, and agent settings
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class LLMBackend(Enum):
    """Supported LLM backends"""
    KAGGLE_PHI4 = "kaggle_phi4"
    OLLAMA = "ollama"
    VLLM = "vllm"
    OPENAI = "openai"
    LOCAL = "local"


@dataclass
class LLMConfig:
    """LLM backend configuration"""
    backend: LLMBackend = LLMBackend.OLLAMA
    api_url: str = "http://localhost:11434"
    model: str = "phi-4"
    max_tokens: int = 4096
    temperature: float = 0.7
    context_window: int = 8192
    timeout: float = 120.0
    api_key: Optional[str] = None
    
    # Fallback chain
    fallback_backends: List[LLMBackend] = field(default_factory=lambda: [
        LLMBackend.OLLAMA,
        LLMBackend.LOCAL
    ])
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load config from environment"""
        backend_str = os.getenv("LLM_BACKEND", "ollama").lower()
        
        backend_map = {
            "kaggle": LLMBackend.KAGGLE_PHI4,
            "kaggle_phi4": LLMBackend.KAGGLE_PHI4,
            "ollama": LLMBackend.OLLAMA,
            "vllm": LLMBackend.VLLM,
            "openai": LLMBackend.OPENAI,
            "local": LLMBackend.LOCAL,
        }
        
        return cls(
            backend=backend_map.get(backend_str, LLMBackend.OLLAMA),
            api_url=os.getenv("LLM_API_URL", "http://localhost:11434"),
            model=os.getenv("LLM_MODEL", "phi-4"),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            context_window=int(os.getenv("LLM_CONTEXT_WINDOW", "8192")),
            timeout=float(os.getenv("LLM_TIMEOUT", "120")),
            api_key=os.getenv("LLM_API_KEY") or os.getenv("KAGGLE_API_KEY"),
        )


# Default backend configurations
BACKEND_PRESETS: Dict[LLMBackend, Dict[str, Any]] = {
    LLMBackend.KAGGLE_PHI4: {
        "api_url": "https://api.kaggle.com/api/v1",
        "model": "microsoft/phi-4",
        "context_window": 16384,
        "max_tokens": 4096,
    },
    LLMBackend.OLLAMA: {
        "api_url": "http://localhost:11434",
        "model": "phi4",
        "context_window": 8192,
        "max_tokens": 4096,
    },
    LLMBackend.VLLM: {
        "api_url": "http://localhost:8000",
        "model": "microsoft/phi-4",
        "context_window": 16384,
        "max_tokens": 4096,
    },
    LLMBackend.OPENAI: {
        "api_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "context_window": 128000,
        "max_tokens": 4096,
    },
    LLMBackend.LOCAL: {
        "api_url": "http://localhost:8080",
        "model": "local",
        "context_window": 4096,
        "max_tokens": 2048,
    },
}


@dataclass
class AgentConfig:
    """Autonomous agent configuration"""
    max_iterations: int = 50
    max_tool_retries: int = 3
    thinking_budget: int = 1000
    enable_streaming: bool = True
    auto_escalate: bool = True
    
    # Phase timeouts (seconds)
    phase_timeouts: Dict[str, int] = field(default_factory=lambda: {
        "reconnaissance": 300,
        "scanning": 600,
        "enumeration": 300,
        "exploitation": 900,
        "post_exploitation": 600,
    })
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        return cls(
            max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "50")),
            max_tool_retries=int(os.getenv("AGENT_MAX_RETRIES", "3")),
            enable_streaming=os.getenv("AGENT_STREAMING", "true").lower() == "true",
        )


@dataclass  
class ToolConfig:
    """Tool executor configuration"""
    allowed_tools: List[str] = field(default_factory=lambda: [
        "nmap", "gobuster", "nikto", "curl", "wget",
        "sshpass", "ftp", "nc", "netcat",
        "dirb", "wfuzz", "ffuf",
        "sqlmap", "hydra", "john",
        "searchsploit", "msfconsole",
        "cat", "grep", "find", "ls", "id", "whoami",
    ])
    
    blocked_patterns: List[str] = field(default_factory=lambda: [
        "rm -rf /", "mkfs", "dd if=", ":(){:|:};",
        "> /dev/sda", "chmod 777 /",
    ])
    
    timeout: int = 300
    max_output_size: int = 100000
    
    @classmethod
    def from_env(cls) -> "ToolConfig":
        return cls(
            timeout=int(os.getenv("TOOL_TIMEOUT", "300")),
            max_output_size=int(os.getenv("TOOL_MAX_OUTPUT", "100000")),
        )


@dataclass
class RedClawConfig:
    """Master configuration"""
    llm: LLMConfig = field(default_factory=LLMConfig.from_env)
    agent: AgentConfig = field(default_factory=AgentConfig.from_env)
    tools: ToolConfig = field(default_factory=ToolConfig.from_env)
    
    workspace: Path = field(default_factory=lambda: Path.home() / ".redclaw")
    debug: bool = False
    verbose: bool = True
    
    @classmethod
    def load(cls) -> "RedClawConfig":
        """Load full configuration"""
        config = cls()
        config.workspace.mkdir(parents=True, exist_ok=True)
        config.debug = os.getenv("REDCLAW_DEBUG", "false").lower() == "true"
        config.verbose = os.getenv("REDCLAW_VERBOSE", "true").lower() == "true"
        return config


# Global config instance
_config: Optional[RedClawConfig] = None


def get_config() -> RedClawConfig:
    """Get or create global config"""
    global _config
    if _config is None:
        _config = RedClawConfig.load()
    return _config


def configure_backend(backend: LLMBackend, **kwargs) -> LLMConfig:
    """Configure LLM backend with preset + overrides"""
    preset = BACKEND_PRESETS.get(backend, {})
    merged = {**preset, **kwargs}
    
    return LLMConfig(
        backend=backend,
        api_url=merged.get("api_url", "http://localhost:11434"),
        model=merged.get("model", "phi-4"),
        max_tokens=merged.get("max_tokens", 4096),
        context_window=merged.get("context_window", 8192),
        temperature=merged.get("temperature", 0.7),
        timeout=merged.get("timeout", 120.0),
        api_key=merged.get("api_key"),
    )
