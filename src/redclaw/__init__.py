"""
RedClaw - Autonomous Penetration Testing System

A local LLM-powered autonomous penetration testing framework
inspired by Claude Code's agentic architecture.
"""

__version__ = "0.1.0"
__author__ = "SparkStack Systems"
__description__ = "Autonomous Penetration Testing System"

# Core components
from .core.llm_client import RedClawLLM, get_llm_client
from .core.orchestrator import AgentOrchestrator
from .core.state_machine import StateMachine
from .core.memory import MemoryManager, get_memory_manager
from .core.rag import RAGSystem, get_rag_system

# Agents
from .agents.recon_agent import ReconAgent
from .agents.scanning_agent import ScanningAgent
from .agents.exploitation_agent import ExploitationAgent
from .agents.post_exploitation_agent import PostExploitationAgent
from .agents.reporting_agent import ReportingAgent

# Tools
from .tools.executor import ToolExecutor

# Integrations
from .integrations.hexstrike import HexStrikeClient, get_hexstrike_client
from .integrations.database import DatabaseManager, get_database

__all__ = [
    # Version
    "__version__",
    "__author__",
    
    # Core
    "RedClawLLM",
    "get_llm_client",
    "AgentOrchestrator",
    "StateMachine",
    "MemoryManager",
    "get_memory_manager",
    "RAGSystem",
    "get_rag_system",
    
    # Agents
    "ReconAgent",
    "ScanningAgent",
    "ExploitationAgent",
    "PostExploitationAgent",
    "ReportingAgent",
    
    # Tools
    "ToolExecutor",
    
    # Integrations
    "HexStrikeClient",
    "get_hexstrike_client",
    "DatabaseManager",
    "get_database"
]
