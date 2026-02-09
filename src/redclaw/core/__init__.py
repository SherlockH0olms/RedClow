"""
RedClaw Core Components
"""

from .llm_client import RedClawLLM, Message, LLMResponse, StreamChunk, get_llm_client
from .orchestrator import ScenarioOrchestrator, ScenarioState, AgentTask, AttackPlan
from .state_machine import StateMachine, Phase, ActionResult, WorkflowContext
from .memory import MemoryManager, MemoryEntry, AttackPattern
from .rag import RAGSystem, RAGDocument, RAGResult
from .config import (
    RedClawConfig, LLMConfig, AgentConfig, ToolConfig,
    LLMBackend, BACKEND_PRESETS, get_config, configure_backend
)
from .llm_manager import LLMManager, get_llm_manager, configure_llm

__all__ = [
    # LLM
    "RedClawLLM",
    "Message",
    "LLMResponse",
    "StreamChunk",
    "get_llm_client",
    # LLM Manager
    "LLMManager",
    "get_llm_manager",
    "configure_llm",
    # Config
    "RedClawConfig",
    "LLMConfig",
    "AgentConfig",
    "ToolConfig",
    "LLMBackend",
    "BACKEND_PRESETS",
    "get_config",
    "configure_backend",
    # Orchestrator
    "ScenarioOrchestrator",
    "ScenarioState",
    "AgentTask",
    "AttackPlan",
    # State Machine
    "StateMachine",
    "Phase",
    "ActionResult",
    "WorkflowContext",
    # Memory
    "MemoryManager",
    "MemoryEntry",
    "AttackPattern",
    # RAG
    "RAGSystem",
    "RAGDocument",
    "RAGResult",
]

