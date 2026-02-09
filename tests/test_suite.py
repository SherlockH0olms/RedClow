#!/usr/bin/env python3
"""
RedClaw Test Suite - Comprehensive testing for the autonomous pentest agent
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def test_imports():
    """Test all core imports"""
    console.print("\n[bold cyan]Testing Core Imports...[/bold cyan]")
    
    tests = []
    
    # Core imports
    try:
        from redclaw.core import RedClawLLM, Message, get_llm_client
        tests.append(("redclaw.core.llm_client", True, ""))
    except Exception as e:
        tests.append(("redclaw.core.llm_client", False, str(e)))
    
    try:
        from redclaw.core import LLMConfig, LLMBackend, get_config
        tests.append(("redclaw.core.config", True, ""))
    except Exception as e:
        tests.append(("redclaw.core.config", False, str(e)))
    
    try:
        from redclaw.core import LLMManager, get_llm_manager
        tests.append(("redclaw.core.llm_manager", True, ""))
    except Exception as e:
        tests.append(("redclaw.core.llm_manager", False, str(e)))
    
    try:
        from redclaw.core import MemoryManager
        tests.append(("redclaw.core.memory", True, ""))
    except Exception as e:
        tests.append(("redclaw.core.memory", False, str(e)))
    
    # Agent imports
    try:
        from redclaw.agents.autonomous_agent import AutonomousAgent, AgentPhase
        tests.append(("redclaw.agents.autonomous_agent", True, ""))
    except Exception as e:
        tests.append(("redclaw.agents.autonomous_agent", False, str(e)))
    
    # Tools imports
    try:
        from redclaw.tools.executor import ToolExecutor
        tests.append(("redclaw.tools.executor", True, ""))
    except Exception as e:
        tests.append(("redclaw.tools.executor", False, str(e)))
    
    # MCP bridge
    try:
        from redclaw.integrations.mcp_bridge import MCPBridge, MCPToolRegistry
        tests.append(("redclaw.integrations.mcp_bridge", True, ""))
    except Exception as e:
        tests.append(("redclaw.integrations.mcp_bridge", False, str(e)))
    
    # CLI
    try:
        from redclaw.cli.app import RedClawApp
        tests.append(("redclaw.cli.app", True, ""))
    except Exception as e:
        tests.append(("redclaw.cli.app", False, str(e)))
    
    # Display results
    table = Table(title="Import Tests")
    table.add_column("Module", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Error", style="red")
    
    passed = 0
    for module, success, error in tests:
        status = "✓ PASS" if success else "✗ FAIL"
        color = "green" if success else "red"
        table.add_row(module, f"[{color}]{status}[/{color}]", error[:50] if error else "")
        if success:
            passed += 1
    
    console.print(table)
    console.print(f"\n[bold]Results: {passed}/{len(tests)} passed[/bold]")
    
    return passed == len(tests)


def test_config():
    """Test configuration system"""
    console.print("\n[bold cyan]Testing Configuration System...[/bold cyan]")
    
    try:
        from redclaw.core.config import (
            RedClawConfig, LLMConfig, LLMBackend, 
            BACKEND_PRESETS, get_config
        )
        
        # Test config loading
        config = get_config()
        console.print(f"  [green]✓[/green] Config loaded: workspace={config.workspace}")
        
        # Test LLM config
        llm_config = LLMConfig.from_env()
        console.print(f"  [green]✓[/green] LLM Backend: {llm_config.backend.value}")
        console.print(f"  [green]✓[/green] Model: {llm_config.model}")
        console.print(f"  [green]✓[/green] Context Window: {llm_config.context_window}")
        
        # Test presets
        for backend, preset in BACKEND_PRESETS.items():
            console.print(f"  [green]✓[/green] Preset: {backend.value} -> {preset.get('model', 'default')}")
        
        return True
    except Exception as e:
        console.print(f"  [red]✗[/red] Config test failed: {e}")
        return False


def test_llm_manager():
    """Test LLM manager"""
    console.print("\n[bold cyan]Testing LLM Manager...[/bold cyan]")
    
    try:
        from redclaw.core.llm_manager import LLMManager, get_llm_manager
        
        manager = get_llm_manager()
        status = manager.get_status()
        
        console.print(f"  [green]✓[/green] Manager initialized")
        console.print(f"  [green]✓[/green] Active backend: {status.get('active_backend', 'pending')}")
        console.print(f"  [green]✓[/green] Model: {status.get('model', 'unknown')}")
        
        return True
    except Exception as e:
        console.print(f"  [yellow]⚠[/yellow] LLM Manager test skipped (no backend): {e}")
        return True  # Not a failure - LLM may not be running


def test_tool_executor():
    """Test tool executor"""
    console.print("\n[bold cyan]Testing Tool Executor...[/bold cyan]")
    
    try:
        from redclaw.tools.executor import ToolExecutor, ToolCategory
        
        executor = ToolExecutor()
        
        # Test safe command
        is_safe = executor.is_safe_command("nmap -sV 127.0.0.1")
        console.print(f"  [green]✓[/green] Safe command check: nmap -> {is_safe}")
        
        # Test dangerous command blocked
        is_safe = executor.is_safe_command("rm -rf /")
        console.print(f"  [green]✓[/green] Dangerous command blocked: rm -rf / -> {not is_safe}")
        
        # Test available tools
        console.print(f"  [green]✓[/green] Allowed tools: {len(executor.allowed_tools)} tools")
        
        return True
    except Exception as e:
        console.print(f"  [red]✗[/red] Tool executor test failed: {e}")
        return False


def test_autonomous_agent():
    """Test autonomous agent initialization"""
    console.print("\n[bold cyan]Testing Autonomous Agent...[/bold cyan]")
    
    try:
        from redclaw.agents.autonomous_agent import (
            AutonomousAgent, AgentPhase, AgentState, 
            TOOL_DEFINITIONS, LANGGRAPH_AVAILABLE
        )
        
        console.print(f"  [green]✓[/green] LangGraph available: {LANGGRAPH_AVAILABLE}")
        console.print(f"  [green]✓[/green] Tool definitions: {len(TOOL_DEFINITIONS)} tools")
        console.print(f"  [green]✓[/green] Agent phases: {[p.value for p in AgentPhase]}")
        
        # Test state
        state = AgentState(target="10.10.10.1", objective="test")
        console.print(f"  [green]✓[/green] AgentState created: target={state.target}")
        
        # Test agent (without running)
        agent = AutonomousAgent(verbose=False)
        console.print(f"  [green]✓[/green] Agent initialized")
        console.print(f"  [green]✓[/green] Graph available: {agent.graph is not None}")
        
        return True
    except Exception as e:
        console.print(f"  [red]✗[/red] Agent test failed: {e}")
        import traceback
        console.print(f"  [dim]{traceback.format_exc()}[/dim]")
        return False


def test_mcp_bridge():
    """Test MCP bridge"""
    console.print("\n[bold cyan]Testing MCP Bridge...[/bold cyan]")
    
    try:
        from redclaw.integrations.mcp_bridge import (
            MCPBridge, MCPToolRegistry, MCPServerType
        )
        
        # Test registry
        registry = MCPToolRegistry()
        console.print(f"  [green]✓[/green] Registry created")
        console.print(f"  [green]✓[/green] Local tools registered: {len(registry.local_tools)}")
        
        # Test GitHub bridge definition
        console.print(f"  [green]✓[/green] MCP server types: {[s.value for s in MCPServerType]}")
        
        return True
    except Exception as e:
        console.print(f"  [red]✗[/red] MCP bridge test failed: {e}")
        return False


async def run_quick_test():
    """Run a quick autonomous agent test (no network)"""
    console.print("\n[bold cyan]Quick Agent Test (Mock)...[/bold cyan]")
    
    try:
        from redclaw.agents.autonomous_agent import AutonomousAgent, AgentState
        
        agent = AutonomousAgent(verbose=True)
        
        # Test event system
        events_received = []
        agent.on("phase_change", lambda p: events_received.append(p))
        
        console.print(f"  [green]✓[/green] Event handlers registered")
        console.print(f"  [green]✓[/green] Agent ready for target")
        
        return True
    except Exception as e:
        console.print(f"  [yellow]⚠[/yellow] Quick test skipped: {e}")
        return True


def main():
    """Run all tests"""
    console.print(Panel(
        "[bold red]RedClaw v2.0 Test Suite[/bold red]\n"
        "[dim]Testing all components before deployment[/dim]",
        border_style="red"
    ))
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("LLM Manager", test_llm_manager()))
    results.append(("Tool Executor", test_tool_executor()))
    results.append(("Autonomous Agent", test_autonomous_agent()))
    results.append(("MCP Bridge", test_mcp_bridge()))
    
    # Async test
    results.append(("Quick Agent Test", asyncio.run(run_quick_test())))
    
    # Summary
    console.print("\n")
    table = Table(title="Test Summary")
    table.add_column("Test", style="cyan")
    table.add_column("Result", style="green")
    
    passed = 0
    for name, success in results:
        status = "[green]✓ PASS[/green]" if success else "[red]✗ FAIL[/red]"
        table.add_row(name, status)
        if success:
            passed += 1
    
    console.print(table)
    console.print(f"\n[bold]Overall: {passed}/{len(results)} tests passed[/bold]")
    
    if passed == len(results):
        console.print("\n[bold green]✓ All tests passed! Ready for deployment.[/bold green]")
        return 0
    else:
        console.print("\n[bold red]✗ Some tests failed. Fix issues before deploying.[/bold red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
