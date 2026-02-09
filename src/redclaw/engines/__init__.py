"""
RedClaw Engines Package
Offensive tool integrations
"""

from .caldera_client import CALDERAClient, Operation, Agent, Ability, OperationState
from .metasploit_client import MetasploitClient, MsfSession, MsfJob, ExploitResult
from .hexstrike_client import HexStrikeClient, HexStrikeFallback, ScanType, AttackType, ScanResult, AttackResult

__all__ = [
    # CALDERA
    "CALDERAClient",
    "Operation",
    "Agent",
    "Ability",
    "OperationState",
    # Metasploit
    "MetasploitClient",
    "MsfSession",
    "MsfJob",
    "ExploitResult",
    # HexStrike
    "HexStrikeClient",
    "HexStrikeFallback",
    "ScanType",
    "AttackType",
    "ScanResult",
    "AttackResult",
]
