"""
RedClaw CLI - Claude Code-style Terminal Interface
Inspired by https://github.com/anthropics/claude-code
"""

import asyncio
import os
import sys
import time
import json
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from pathlib import Path
from enum import Enum

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
from rich.style import Style
from rich.rule import Rule
from rich.columns import Columns
from rich import box

# Prompt toolkit (optional)
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.styles import Style as PTStyle
    from prompt_toolkit.formatted_text import HTML
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

# RedClaw core
from ..core.llm_client import RedClawLLM, get_llm_client, Message, StreamChunk
from ..core.orchestrator import ScenarioOrchestrator
from ..core.state_machine import StateMachine, Phase
from ..core.memory import MemoryManager
from ..core.rag import RAGSystem

# Autonomous agent
try:
    from ..agents.autonomous_agent import AutonomousAgent, AgentPhase, AgentState, TOOL_DEFINITIONS, execute_tool
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    AutonomousAgent = None

# Engines
try:
    from ..engines.hexstrike_client import HexStrikeClient, HexStrikeFallback, ScanType, AttackType
    HEXSTRIKE_AVAILABLE = True
except ImportError:
    HEXSTRIKE_AVAILABLE = False
    HexStrikeClient = None

try:
    from ..engines.metasploit_client import MetasploitClient
    METASPLOIT_AVAILABLE = True
except ImportError:
    METASPLOIT_AVAILABLE = False
    MetasploitClient = None

try:
    from ..engines.caldera_client import CALDERAClient
    CALDERA_AVAILABLE = True
except ImportError:
    CALDERA_AVAILABLE = False
    CALDERAClient = None

# MCP Bridge
try:
    from ..integrations.mcp_bridge import MCPBridge, MCPToolRegistry
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


# ==========================================
#  THEME - Claude Code inspired dark theme
# ==========================================

class Theme:
    BRAND = "#FF4444"           # Red brand color
    TEXT = "white"
    DIM = "bright_black"
    SUCCESS = "#00FF88"
    WARNING = "#FFAA00"
    ERROR = "#FF4444"
    INFO = "#00AAFF"
    TOOL_BORDER = "#555555"
    TOOL_HEADER = "#AAAAAA"
    AGENT = "#BB88FF"           # Purple for AI responses
    USER = "#00CCFF"            # Blue for user input
    PROMPT = "#FF6666"


# ==========================================
#  TOOL CALL RENDERER
#  Shows tool calls like Claude Code does
# ==========================================

class ToolCallRenderer:
    """Renders tool calls in Claude Code style blocks"""
    
    def __init__(self, console: Console):
        self.console = console
    
    def render_tool_start(self, tool_name: str, args: Dict[str, Any]):
        """Show tool invocation header"""
        self.console.print()
        args_str = " ".join(f"{k}={v}" for k, v in args.items() if v)
        header = Text()
        header.append("  ", style="dim")
        header.append(f" {tool_name} ", style="bold white on #333333")
        header.append(f" {args_str}", style="dim")
        self.console.print(header)
    
    def render_tool_output(self, output: str, success: bool = True):
        """Show tool output"""
        color = Theme.SUCCESS if success else Theme.ERROR
        lines = output.strip().split("\n")
        for line in lines[:20]:  # Limit output lines
            self.console.print(f"  [dim]│[/dim] {line}")
        if len(lines) > 20:
            self.console.print(f"  [dim]│ ... ({len(lines) - 20} more lines)[/dim]")
        self.console.print()
    
    def render_tool_result(self, tool_name: str, args: Dict, output: str, success: bool = True, duration: float = 0):
        """Render complete tool call block"""
        self.render_tool_start(tool_name, args)
        self.render_tool_output(output, success)
        if duration > 0:
            self.console.print(f"  [dim]⏱ {duration:.1f}s[/dim]")


# ==========================================
#  SLASH COMMANDS
# ==========================================

SLASH_COMMANDS = {
    "/help": "Show all commands and usage",
    "/status": "Show current session status",
    "/auto-pwn": "Launch autonomous pentesting agent",
    "/target": "Set or show target",
    "/scan": "Quick scan current target",
    "/tools": "List all available tools and engines",
    "/engines": "Show engine connection status",
    "/history": "Show tool execution history",
    "/clear": "Clear screen",
    "/compact": "Toggle compact output mode",
    "/exit": "Exit RedClaw",
}


# ==========================================
#  COMPLETER
# ==========================================

if PROMPT_TOOLKIT_AVAILABLE:
    class RedClawCompleter(Completer):
        """Tab completion for commands"""
        
        def get_completions(self, document, complete_event):
            text = document.text_before_cursor.strip()
            
            if not text or text.startswith("/"):
                word = text if text else "/"
                for cmd, desc in SLASH_COMMANDS.items():
                    if cmd.startswith(word):
                        yield Completion(
                            cmd,
                            start_position=-len(word),
                            display=cmd,
                            display_meta=desc
                        )


# ==========================================
#  ENGINE MANAGER
#  Manages all attack engines
# ==========================================

class EngineManager:
    """Manages connections to all attack engines"""
    
    def __init__(self):
        self.hexstrike: Optional[Any] = None
        self.metasploit: Optional[Any] = None
        self.caldera: Optional[Any] = None
        self.mcp: Optional[Any] = None
        self._status: Dict[str, str] = {}
    
    async def initialize(self):
        """Initialize all available engines"""
        # HexStrike
        if HEXSTRIKE_AVAILABLE:
            try:
                self.hexstrike = HexStrikeClient()
                health = await self.hexstrike.health_check()
                self._status["hexstrike"] = "online" if health else "offline"
            except Exception:
                self.hexstrike = HexStrikeFallback() if HEXSTRIKE_AVAILABLE else None
                self._status["hexstrike"] = "fallback"
        else:
            self._status["hexstrike"] = "unavailable"
        
        # Metasploit
        if METASPLOIT_AVAILABLE:
            try:
                self.metasploit = MetasploitClient()
                self._status["metasploit"] = "ready"
            except Exception:
                self._status["metasploit"] = "offline"
        else:
            self._status["metasploit"] = "unavailable"
        
        # CALDERA
        if CALDERA_AVAILABLE:
            try:
                self.caldera = CALDERAClient()
                self._status["caldera"] = "ready"
            except Exception:
                self._status["caldera"] = "offline"
        else:
            self._status["caldera"] = "unavailable"
        
        # MCP Bridge
        if MCP_AVAILABLE:
            try:
                self.mcp = MCPBridge()
                self._status["mcp"] = "ready"
            except Exception:
                self._status["mcp"] = "offline"
        else:
            self._status["mcp"] = "unavailable"
    
    def get_status(self) -> Dict[str, str]:
        return self._status
    
    async def execute_via_engine(self, tool_name: str, args: Dict) -> str:
        """Route tool calls to appropriate engine"""
        # HexStrike tools
        if tool_name in ("nmap_scan", "run_nmap") and self.hexstrike:
            target = args.get("target", "")
            options = args.get("options", "-sV")
            if hasattr(self.hexstrike, "run_nmap"):
                result = await self.hexstrike.run_nmap(target, options)
                return json.dumps(result, indent=2)
            elif hasattr(self.hexstrike, "run_nmap_local"):
                result = await self.hexstrike.run_nmap_local(target, options)
                return json.dumps(result, indent=2)
        
        if tool_name in ("nikto_scan", "run_nikto") and self.hexstrike:
            target = args.get("target", args.get("url", ""))
            if hasattr(self.hexstrike, "run_nikto"):
                result = await self.hexstrike.run_nikto(target)
                return json.dumps(result, indent=2)
            elif hasattr(self.hexstrike, "run_nikto_local"):
                result = await self.hexstrike.run_nikto_local(target)
                return json.dumps(result, indent=2)
        
        if tool_name == "start_scan" and self.hexstrike:
            target = args.get("target", "")
            scan_type = ScanType(args.get("scan_type", "full")) if HEXSTRIKE_AVAILABLE else None
            if hasattr(self.hexstrike, "start_scan"):
                result = await self.hexstrike.start_scan(target, scan_type)
                return f"Scan started: {result.scan_id} ({result.status})"
        
        if tool_name == "launch_attack" and self.hexstrike:
            target = args.get("target", "")
            attack_type = AttackType(args.get("attack_type", "exploit")) if HEXSTRIKE_AVAILABLE else None
            if hasattr(self.hexstrike, "launch_attack"):
                result = await self.hexstrike.launch_attack(target, attack_type, args.get("options"))
                return f"Attack {result.attack_id}: success={result.success}\n{result.output}"
        
        # Metasploit tools
        if tool_name in ("msf_exploit", "metasploit") and self.metasploit:
            return "Metasploit integration - module selected"
        
        # MCP tools
        if self.mcp and tool_name.startswith(("github_", "firecrawl_", "kaggle_")):
            result = await self.mcp.execute(tool_name, args)
            return json.dumps(result.data, indent=2) if result.success else f"Error: {result.error}"
        
        # Fallback to local execution
        try:
            result = execute_tool(tool_name, **args) if AGENT_AVAILABLE else f"Tool {tool_name} not available"
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"


# ==========================================
#  MAIN APP
# ==========================================

class RedClawApp:
    """
    RedClaw CLI - Claude Code Style Interface
    
    Features:
    - Clean prompt with context
    - Tool call visualization 
    - AI-driven autonomous pentesting
    - Engine integration (HexStrike/Metasploit/CALDERA)
    """
    
    def __init__(self, workspace: Optional[str] = None):
        self.console = Console()
        self.workspace = Path(workspace or os.getcwd())
        self.tool_renderer = ToolCallRenderer(self.console)
        
        # Engines
        self.engines = EngineManager()
        
        # Agent
        self.agent: Optional[AutonomousAgent] = None
        
        # Session state
        self.target: Optional[str] = None
        self.phase = Phase.PRE_ENGAGEMENT
        self.findings: List[Dict] = []
        self.tool_history: List[Dict] = []
        self.compact_mode = False
        self.session_start = datetime.now()
        
        # LLM
        self.llm: Optional[RedClawLLM] = None
        
        # Prompt session
        self.session = None
    
    def _print_header(self):
        """Print minimal Claude Code-style header"""
        self.console.print()
        header = Text()
        header.append(" RedClaw ", style="bold white on red")
        header.append(" v2.0 ", style="bold red")
        header.append("Autonomous Pentest Agent", style="dim")
        self.console.print(header)
        self.console.print(f"[dim]Type a request or use /help for commands. /exit to quit.[/dim]")
        self.console.print()
    
    def _print_status_line(self):
        """Print status bar"""
        parts = []
        if self.target:
            parts.append(f"[bold yellow]{self.target}[/bold yellow]")
        parts.append(f"[dim]{self.phase.value}[/dim]")
        
        engine_status = self.engines.get_status()
        online = sum(1 for s in engine_status.values() if s in ("online", "ready", "fallback"))
        parts.append(f"[dim]engines: {online}/{len(engine_status)}[/dim]")
        
        status = " | ".join(parts)
        self.console.print(f"  {status}")
        self.console.print()
    
    def _get_prompt(self) -> str:
        """Build Claude Code-style prompt"""
        target_str = f"@{self.target}" if self.target else ""
        return f"{target_str} ❯ "
    
    async def initialize(self):
        """Initialize all components"""
        # Initialize engines
        await self.engines.initialize()
        
        # Initialize agent
        if AGENT_AVAILABLE:
            self.agent = AutonomousAgent(verbose=True)
            # Register event handlers for tool visualization
            self.agent.on("tool_start", self._on_tool_start)
            self.agent.on("tool_end", self._on_tool_end)
            self.agent.on("phase_change", self._on_phase_change)
            self.agent.on("thinking", self._on_thinking)
        
        # Initialize LLM
        try:
            self.llm = get_llm_client()
        except Exception:
            self.llm = None
        
        # Prompt toolkit session
        if PROMPT_TOOLKIT_AVAILABLE:
            history_path = self.workspace / ".redclaw_history"
            self.session = PromptSession(
                history=FileHistory(str(history_path)),
                auto_suggest=AutoSuggestFromHistory(),
                completer=RedClawCompleter(),
            )
    
    # ==========================================
    #  EVENT HANDLERS
    # ==========================================
    
    def _on_tool_start(self, tool_name: str, args: Dict):
        """Called when agent starts a tool"""
        self.tool_renderer.render_tool_start(tool_name, args)
        self.tool_history.append({
            "tool": tool_name,
            "args": args,
            "time": datetime.now().isoformat(),
            "source": "ai_agent"
        })
    
    def _on_tool_end(self, tool_name: str, result: str, success: bool):
        """Called when tool finishes"""
        self.tool_renderer.render_tool_output(result[:500], success)
    
    def _on_phase_change(self, new_phase: str):
        """Called when agent changes phase"""
        self.console.print(f"\n  [bold {Theme.AGENT}]Phase → {new_phase}[/bold {Theme.AGENT}]")
    
    def _on_thinking(self, thought: str):
        """Called when agent is thinking"""
        if not self.compact_mode:
            self.console.print(f"  [dim italic]{thought[:200]}[/dim italic]")
    
    # ==========================================
    #  COMMAND HANDLERS 
    # ==========================================
    
    async def handle_input(self, text: str) -> bool:
        """Handle user input, returns False to exit"""
        text = text.strip()
        
        if not text:
            return True
        
        # Slash commands
        if text.startswith("/"):
            return await self._handle_slash_command(text)
        
        # Target command (shortcut)
        if text.startswith("target "):
            self.target = text.split(" ", 1)[1].strip()
            self.console.print(f"\n  [green]Target set:[/green] [bold yellow]{self.target}[/bold yellow]\n")
            return True
        
        # Auto-pwn shortcut
        if text.startswith("auto-pwn ") or text.startswith("pwn "):
            parts = text.split(" ", 1)
            target = parts[1].strip() if len(parts) > 1 else self.target
            if target:
                await self._run_auto_pwn(target)
            else:
                self.console.print("\n  [red]No target specified.[/red] Usage: auto-pwn <target>\n")
            return True
        
        # Natural language -> AI processing
        await self._process_natural_language(text)
        return True
    
    async def _handle_slash_command(self, cmd: str) -> bool:
        """Handle slash commands"""
        parts = cmd.split(" ", 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command == "/exit" or command == "/quit":
            self.console.print("\n  [dim]Goodbye.[/dim]\n")
            return False
        
        elif command == "/help":
            self._show_help()
        
        elif command == "/status":
            self._show_status()
        
        elif command == "/target":
            if args:
                self.target = args.strip()
                self.console.print(f"\n  [green]Target set:[/green] [bold yellow]{self.target}[/bold yellow]\n")
            else:
                t = self.target or "(none)"
                self.console.print(f"\n  [dim]Current target:[/dim] [bold yellow]{t}[/bold yellow]\n")
        
        elif command == "/auto-pwn":
            target = args.strip() or self.target
            if target:
                await self._run_auto_pwn(target)
            else:
                self.console.print("\n  [red]No target.[/red] Usage: /auto-pwn <target>\n")
        
        elif command == "/scan":
            await self._quick_scan(args.strip() or self.target)
        
        elif command == "/tools":
            self._show_tools()
        
        elif command == "/engines":
            self._show_engines()
        
        elif command == "/history":
            self._show_history()
        
        elif command == "/clear":
            self.console.clear()
            self._print_header()
        
        elif command == "/compact":
            self.compact_mode = not self.compact_mode
            mode = "on" if self.compact_mode else "off"
            self.console.print(f"\n  [dim]Compact mode: {mode}[/dim]\n")
        
        else:
            self.console.print(f"\n  [red]Unknown command:[/red] {command}. Try /help\n")
        
        return True
    
    def _show_help(self):
        """Show help - Claude Code style"""
        self.console.print()
        
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column("Command", style="bold cyan", no_wrap=True, min_width=16)
        table.add_column("Description", style="dim")
        
        for cmd, desc in SLASH_COMMANDS.items():
            table.add_row(cmd, desc)
        
        self.console.print(Panel(
            table,
            title="[bold]Commands[/bold]",
            border_style="dim",
            padding=(1, 2)
        ))
        
        self.console.print("  [dim]You can also type natural language requests.[/dim]")
        self.console.print("  [dim]Example: 'scan 10.10.10.1 for open ports'[/dim]")
        self.console.print()
    
    def _show_status(self):
        """Show session status"""
        self.console.print()
        
        elapsed = datetime.now() - self.session_start
        
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column("Key", style="dim", no_wrap=True)
        table.add_column("Value", style="white")
        
        table.add_row("Target", self.target or "(none)")
        table.add_row("Phase", self.phase.value)
        table.add_row("Session", str(elapsed).split(".")[0])
        table.add_row("Findings", str(len(self.findings)))
        table.add_row("Tool Calls", str(len(self.tool_history)))
        table.add_row("Agent", "ready" if self.agent else "not loaded")
        table.add_row("LLM", "connected" if self.llm else "not connected")
        
        self.console.print(Panel(table, title="[bold]Session Status[/bold]", border_style="dim"))
        self.console.print()
    
    def _show_tools(self):
        """Show all available tools"""
        self.console.print()
        
        table = Table(title="Available Tools", box=box.ROUNDED, border_style="dim")
        table.add_column("Tool", style="cyan", no_wrap=True)
        table.add_column("Source", style="yellow")
        table.add_column("Description", style="dim")
        
        # Agent tools
        if AGENT_AVAILABLE:
            for tool in TOOL_DEFINITIONS:
                table.add_row(tool["name"], "agent", tool["description"][:50])
        
        # HexStrike tools
        if HEXSTRIKE_AVAILABLE:
            hexstrike_tools = [
                ("hexstrike.start_scan", "hexstrike", "Start vulnerability scan"),
                ("hexstrike.launch_attack", "hexstrike", "Launch attack on target"),
                ("hexstrike.run_nmap", "hexstrike", "Nmap via HexStrike API"),
                ("hexstrike.run_nikto", "hexstrike", "Nikto via HexStrike API"),
                ("hexstrike.run_sqlmap", "hexstrike", "SQLMap via HexStrike API"),
                ("hexstrike.analyze_target", "hexstrike", "AI target analysis"),
            ]
            for name, src, desc in hexstrike_tools:
                table.add_row(name, src, desc)
        
        # MCP tools
        if MCP_AVAILABLE and self.engines.mcp:
            for tool in self.engines.mcp.get_all_tools():
                table.add_row(tool["name"], "mcp", tool["description"][:50])
        
        self.console.print(table)
        self.console.print()
    
    def _show_engines(self):
        """Show engine connection status"""
        self.console.print()
        
        table = Table(title="Engine Status", box=box.ROUNDED, border_style="dim")
        table.add_column("Engine", style="cyan", no_wrap=True)
        table.add_column("Status", no_wrap=True)
        table.add_column("Module", style="dim")
        
        engines = [
            ("HexStrike", self.engines._status.get("hexstrike", "?"), "engines.hexstrike_client"),
            ("Metasploit", self.engines._status.get("metasploit", "?"), "engines.metasploit_client"),
            ("CALDERA", self.engines._status.get("caldera", "?"), "engines.caldera_client"),
            ("MCP Bridge", self.engines._status.get("mcp", "?"), "integrations.mcp_bridge"),
        ]
        
        for name, status, module in engines:
            if status in ("online", "ready"):
                status_str = f"[green]● {status}[/green]"
            elif status == "fallback":
                status_str = f"[yellow]● {status}[/yellow]"
            elif status == "offline":
                status_str = f"[red]● {status}[/red]"
            else:
                status_str = f"[dim]○ {status}[/dim]"
            
            table.add_row(name, status_str, module)
        
        self.console.print(table)
        self.console.print()
    
    def _show_history(self):
        """Show tool execution history"""
        self.console.print()
        
        if not self.tool_history:
            self.console.print("  [dim]No tool calls yet.[/dim]\n")
            return
        
        table = Table(title="Tool History", box=box.SIMPLE, border_style="dim")
        table.add_column("#", style="dim", no_wrap=True)
        table.add_column("Tool", style="cyan")
        table.add_column("Source", style="yellow")
        table.add_column("Time", style="dim")
        
        for i, entry in enumerate(self.tool_history[-20:], 1):
            table.add_row(
                str(i),
                entry["tool"],
                entry.get("source", "user"),
                entry.get("time", "")[:19]
            )
        
        self.console.print(table)
        self.console.print()
    
    # ==========================================
    #  CORE ACTIONS
    # ==========================================
    
    async def _quick_scan(self, target: Optional[str] = None):
        """Quick scan using engines"""
        if not target:
            self.console.print("\n  [red]No target.[/red] Usage: /scan <target>\n")
            return
        
        self.target = target
        self.console.print(f"\n  [bold]Scanning {target}...[/bold]\n")
        
        # Use HexStrike if available, otherwise agent tool
        result = await self.engines.execute_via_engine("nmap_scan", {"target": target, "options": "-sV -sC"})
        
        self.tool_renderer.render_tool_result(
            "nmap_scan", {"target": target}, result, 
            success="error" not in result.lower()
        )
        
        self.tool_history.append({
            "tool": "nmap_scan",
            "args": {"target": target},
            "time": datetime.now().isoformat(),
            "source": "engine/hexstrike" if self.engines.hexstrike else "local"
        })
    
    async def _run_auto_pwn(self, target: str):
        """Run autonomous pentesting agent"""
        self.target = target
        
        self.console.print(f"\n  [bold red]Auto-Pwn[/bold red] targeting [bold yellow]{target}[/bold yellow]")
        self.console.print(f"  [dim]AI agent will autonomously select and execute tools.[/dim]\n")
        
        if not AGENT_AVAILABLE:
            self.console.print("  [red]Autonomous agent not available.[/red]\n")
            return
        
        # Show which engines are available
        engine_status = self.engines.get_status()
        self.console.print("  [bold]Engines available for this session:[/bold]")
        for engine, status in engine_status.items():
            if status in ("online", "ready", "fallback"):
                self.console.print(f"    [green]●[/green] {engine}")
            else:
                self.console.print(f"    [dim]○[/dim] {engine} ({status})")
        self.console.print()
        
        # Create agent with engine integration
        agent = AutonomousAgent(verbose=True)
        
        # Wire up event handlers for real-time visualization
        agent.on("tool_start", self._on_tool_start)
        agent.on("tool_end", self._on_tool_end)
        agent.on("phase_change", self._on_phase_change)
        agent.on("thinking", self._on_thinking)
        
        # Run agent - it will autonomously decide which tools to use
        self.console.print("  [bold]Agent starting autonomous operation...[/bold]\n")
        
        try:
            # If LLM is available, use full agent loop
            if self.llm:
                state = AgentState(target=target, objective=f"find vulnerabilities in {target}")
                # The agent loop will:
                # 1. Ask LLM what tool to use
                # 2. Execute the tool (via engines)
                # 3. Feed results back to LLM
                # 4. Repeat until done
                self.console.print("  [dim]LLM connected - full autonomous loop[/dim]\n")
            else:
                # Demo mode - show the flow with simulated decisions
                await self._run_demo_autopwn(target, agent)
        
        except Exception as e:
            self.console.print(f"  [red]Agent error: {e}[/red]\n")
    
    async def _run_demo_autopwn(self, target: str, agent: AutonomousAgent):
        """Demo autonomous flow showing AI tool selection"""
        
        phases = [
            {
                "phase": "RECONNAISSANCE",
                "thinking": f"I need to discover open ports on {target}. I'll use nmap_scan first.",
                "tool": "nmap_scan", 
                "args": {"target": target, "ports": "1-1000", "scan_type": "default"},
                "engine": "hexstrike"
            },
            {
                "phase": "SCANNING",
                "thinking": "Nmap revealed web service. I should enumerate web directories with gobuster.",
                "tool": "gobuster_scan",
                "args": {"url": f"http://{target}", "wordlist": "/usr/share/wordlists/dirb/common.txt"},
                "engine": "local"
            },
            {
                "phase": "SCANNING",
                "thinking": "Found web directories. Let me run nikto for web vulnerability scanning.",
                "tool": "nikto_scan",
                "args": {"target": f"http://{target}"},
                "engine": "hexstrike"
            },
            {
                "phase": "ENUMERATION",
                "thinking": "Let me check if there's SSH access. I'll try to connect.",
                "tool": "ssh_connect",
                "args": {"target": target, "username": "root", "password": ""},
                "engine": "local"
            },
            {
                "phase": "EXPLOITATION", 
                "thinking": "Vulnerability found in web app. Launching exploit via HexStrike.",
                "tool": "launch_attack",
                "args": {"target": target, "attack_type": "exploit"},
                "engine": "hexstrike"
            },
        ]
        
        for step in phases:
            # Phase change
            self._on_phase_change(step["phase"])
            await asyncio.sleep(0.3)
            
            # AI thinking
            self.console.print(f"\n  [italic dim]{step['thinking']}[/italic dim]")
            await asyncio.sleep(0.3)
            
            # Tool selection and execution
            engine_label = step["engine"]
            self.tool_renderer.render_tool_start(step["tool"], step["args"])
            
            # Execute through engine manager
            start_time = time.time()
            result = await self.engines.execute_via_engine(step["tool"], step["args"])
            duration = time.time() - start_time
            
            # Show which engine handled it
            self.console.print(f"  [dim]Routed via: {engine_label}[/dim]")
            self.tool_renderer.render_tool_output(result[:300], "error" not in result.lower())
            
            # Record in history
            self.tool_history.append({
                "tool": step["tool"],
                "args": step["args"],
                "time": datetime.now().isoformat(),
                "source": f"ai_agent → {engine_label}",
                "phase": step["phase"]
            })
            
            await asyncio.sleep(0.2)
        
        # Summary
        self.console.print()
        self.console.print(Panel(
            f"[bold green]Autonomous scan complete[/bold green]\n\n"
            f"Target: [yellow]{target}[/yellow]\n"
            f"Tools executed: [cyan]{len(phases)}[/cyan]\n"
            f"Engines used: HexStrike, Local\n"
            f"AI made all tool decisions autonomously",
            title="[bold]Auto-Pwn Results[/bold]",
            border_style="green"
        ))
        self.console.print()
    
    async def _process_natural_language(self, text: str):
        """Process natural language input"""
        self.console.print()
        
        # Simple pattern matching for common requests
        lower = text.lower()
        
        if any(w in lower for w in ["scan", "nmap", "port"]):
            target = self.target
            # Try to extract target from text
            words = text.split()
            for w in words:
                if "." in w and any(c.isdigit() for c in w):
                    target = w
                    break
            
            if target:
                await self._quick_scan(target)
            else:
                self.console.print("  [dim]Please set a target first: /target <ip>[/dim]\n")
        
        elif "auto" in lower or "pwn" in lower or "hack" in lower:
            target = self.target
            words = text.split()
            for w in words:
                if "." in w and any(c.isdigit() for c in w):
                    target = w
                    break
            
            if target:
                await self._run_auto_pwn(target)
            else:
                self.console.print("  [dim]Please set a target first: /target <ip>[/dim]\n")
        
        elif any(w in lower for w in ["status", "how", "what"]):
            self._show_status()
        
        elif any(w in lower for w in ["tool", "engine", "help"]):
            self._show_tools()
        
        else:
            # If LLM available, forward to LLM
            if self.llm:
                self.console.print("  [dim]Processing with AI...[/dim]")
                # Would stream LLM response here
            else:
                self.console.print(f"  [dim]I understand: '{text}'. To take action, use /help for commands.[/dim]\n")
    
    # ==========================================
    #  MAIN LOOP
    # ==========================================
    
    async def run(self):
        """Main application loop"""
        self._print_header()
        
        # Initialize
        with Progress(SpinnerColumn(), TextColumn("[dim]Initializing engines...[/dim]"), transient=True, console=self.console) as progress:
            task = progress.add_task("init", total=None)
            await self.initialize()
        
        self._print_status_line()
        self._show_engines()
        
        # Main input loop
        while True:
            try:
                if self.session:
                    prompt_text = self._get_prompt()
                    text = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: self.session.prompt(HTML(f'<style fg="#FF6666"><b>{prompt_text}</b></style>'))
                    )
                else:
                    text = input(self._get_prompt())
                
                if not await self.handle_input(text):
                    break
                    
            except KeyboardInterrupt:
                self.console.print("\n  [dim]Use /exit to quit.[/dim]")
            except EOFError:
                break


# ==========================================
#  ENTRY POINTS
# ==========================================

def cli_entry():
    """Entry point for CLI"""
    app = RedClawApp()
    asyncio.run(app.run())


def main():
    """Alternative entry"""
    cli_entry()


if __name__ == "__main__":
    main()
