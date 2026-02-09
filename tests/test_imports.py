#!/usr/bin/env python3
"""
RedClaw v2.0 Import Verification Tests
Verifies all modules can be imported correctly.
"""

import sys
from pathlib import Path

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_core_imports():
    """Test core module imports"""
    print("[*] Testing core imports...")
    
    from redclaw.core import (
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
    
    print("[+] Core imports: OK")
    return True


def test_agent_imports():
    """Test agent module imports"""
    print("[*] Testing agent imports...")
    
    from redclaw.agents import (
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
    
    print("[+] Agent imports: OK")
    return True


def test_ai_redteam_imports():
    """Test AI Red Teaming module imports"""
    print("[*] Testing AI Red Team imports...")
    
    from redclaw.ai_redteam import (
        PyRITClient,
        AttackStrategy,
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
    
    print("[+] AI Red Team imports: OK")
    return True


def test_engine_imports():
    """Test engine module imports"""
    print("[*] Testing engine imports...")
    
    from redclaw.engines import (
        CALDERAClient,
        Operation,
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
    )
    
    print("[+] Engine imports: OK")
    return True


def test_cli_imports():
    """Test CLI module imports"""
    print("[*] Testing CLI imports...")
    
    from redclaw.cli import RedClawApp
    
    print("[+] CLI imports: OK")
    return True


def test_main_package():
    """Test main package imports"""
    print("[*] Testing main package imports...")
    
    from redclaw import (
        __version__,
        RedClawLLM,
        ReconAgent,
        ExploitAgent,
        PostExploitAgent,
        PyRITClient,
        AutoRedTeamer,
        HARMFramework,
        CuriosityAgent,
        CALDERAClient,
        MetasploitClient,
        HexStrikeClient,
    )
    
    print(f"[+] RedClaw v{__version__} imports: OK")
    return True


def run_all_tests():
    """Run all import tests"""
    print("=" * 60)
    print("RedClaw v2.0 Import Verification")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Core", test_core_imports()))
    except Exception as e:
        print(f"[-] Core imports FAILED: {e}")
        results.append(("Core", False))
    
    try:
        results.append(("Agents", test_agent_imports()))
    except Exception as e:
        print(f"[-] Agent imports FAILED: {e}")
        results.append(("Agents", False))
    
    try:
        results.append(("AI RedTeam", test_ai_redteam_imports()))
    except Exception as e:
        print(f"[-] AI RedTeam imports FAILED: {e}")
        results.append(("AI RedTeam", False))
    
    try:
        results.append(("Engines", test_engine_imports()))
    except Exception as e:
        print(f"[-] Engine imports FAILED: {e}")
        results.append(("Engines", False))
    
    try:
        results.append(("CLI", test_cli_imports()))
    except Exception as e:
        print(f"[-] CLI imports FAILED: {e}")
        results.append(("CLI", False))
    
    try:
        results.append(("Main Package", test_main_package()))
    except Exception as e:
        print(f"[-] Main package imports FAILED: {e}")
        results.append(("Main Package", False))
    
    print("=" * 60)
    print("Summary:")
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("[+] All imports verified successfully!")
        return 0
    else:
        print("[-] Some imports failed!")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
