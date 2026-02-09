"""
RedClaw v2 - Advanced Autonomous Red Team AI Agent
===================================================

A production-ready AI-powered penetration testing framework
with advanced offensive capabilities, local LLM integration,
and comprehensive security tool orchestration.

Components:
- Core: LLM client, orchestrator, state machine, memory, RAG
- Agents: Recon, Exploit, Post-Exploitation specialists
- AI RedTeam: PyRIT, AutoRedTeamer, HARM, Curiosity Agent
- Engines: CALDERA, Metasploit, HexStrike clients
- CLI: Interactive Claude Code-like interface

Usage:
    from redclaw import RedClawLLM, ScenarioOrchestrator, ReconAgent
    from redclaw.cli import RedClawApp
    
    app = RedClawApp()
    app.run()
"""

__version__ = "2.0.0"
__author__ = "SparkStack Systems"

# Core components (matching actual exports from core/__init__.py)
from .core import (
    RedClawLLM,
    Message,
    LLMResponse,
    StreamChunk,
    get_llm_client,
    ScenarioOrchestrator,
    ScenarioState,
    AgentTask,
    AttackPlan,
    StateMachine,
    Phase,
    ActionResult,
    WorkflowContext,
    MemoryManager,
    MemoryEntry,
    AttackPattern,
    RAGSystem,
    RAGDocument,
    RAGResult,
)

# Agents
from .agents import (
    BaseAgent,
    AgentCapability,
    AgentResult,
    AgentState,
    ReconAgent,
    ReconFinding,
    ExploitAgent,
    ExploitChainAgent,
    ExploitAttempt,
    PostExploitAgent,
    CollectedData,
)

# AI Red Teaming
from .ai_redteam import (
    PyRITClient,
    AttackStrategy,
    AttackResult as PyRITAttackResult,
    PyRITSession,
    AutoRedTeamer,
    RedTeamSession,
    AttackPhase,
    HARMFramework,
    HarmCategory,
    HarmReport,
    HarmSeverity,
    CuriosityAgent,
    CuriositySession,
    ExplorationState,
)

# Engines
from .engines import (
    CALDERAClient,
    Operation,
    Agent as CALDERAAgent,
    Ability,
    OperationState,
    MetasploitClient,
    MsfSession,
    MsfJob,
    ExploitResult,
    HexStrikeClient,
    HexStrikeFallback,
    ScanType,
    AttackType,
    ScanResult,
    AttackResult as HexStrikeAttackResult,
)

# CLI
from .cli import RedClawApp

__all__ = [
    # Version
    "__version__",
    # Core - LLM
    "RedClawLLM",
    "Message",
    "LLMResponse",
    "StreamChunk",
    "get_llm_client",
    # Core - Orchestrator
    "ScenarioOrchestrator",
    "ScenarioState",
    "AgentTask",
    "AttackPlan",
    # Core - State Machine
    "StateMachine",
    "Phase",
    "ActionResult",
    "WorkflowContext",
    # Core - Memory
    "MemoryManager",
    "MemoryEntry",
    "AttackPattern",
    # Core - RAG
    "RAGSystem",
    "RAGDocument",
    "RAGResult",
    # Agents
    "BaseAgent",
    "AgentCapability",
    "AgentResult",
    "AgentState",
    "ReconAgent",
    "ReconFinding",
    "ExploitAgent",
    "ExploitChainAgent",
    "ExploitAttempt",
    "PostExploitAgent",
    "CollectedData",
    # AI RedTeam
    "PyRITClient",
    "AttackStrategy",
    "PyRITAttackResult",
    "PyRITSession",
    "AutoRedTeamer",
    "RedTeamSession",
    "AttackPhase",
    "HARMFramework",
    "HarmCategory",
    "HarmReport",
    "HarmSeverity",
    "CuriosityAgent",
    "CuriositySession",
    "ExplorationState",
    # Engines
    "CALDERAClient",
    "Operation",
    "CALDERAAgent",
    "Ability",
    "OperationState",
    "MetasploitClient",
    "MsfSession",
    "MsfJob",
    "ExploitResult",
    "HexStrikeClient",
    "HexStrikeFallback",
    "ScanType",
    "AttackType",
    "HexStrikeAttackResult",
    "ScanResult",
    # CLI
    "RedClawApp",
]
