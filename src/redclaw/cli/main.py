"""
RedClaw CLI - Interactive Command Line Interface
Full integration with all agents and components
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

# Import core components
from ..core.llm_client import get_llm_client, RedClawLLM
from ..core.orchestrator import AgentOrchestrator, Phase
from ..core.state_machine import StateMachine, ActionResult
from ..core.memory import get_memory_manager, MemoryManager
from ..core.rag import get_rag_system, RAGSystem

# Import agents
from ..agents.recon_agent import ReconAgent
from ..agents.scanning_agent import ScanningAgent
from ..agents.exploitation_agent import ExploitationAgent
from ..agents.post_exploitation_agent import PostExploitationAgent
from ..agents.reporting_agent import ReportingAgent

# Import tools
from ..tools.executor import ToolExecutor

# Import integrations
from ..integrations.hexstrike import get_hexstrike_client


class RedClawCLI:
    """
    RedClaw Interactive CLI
    
    Full-featured terminal interface with:
    - Rich formatting
    - Session management
    - All agent integrations
    - Real-time progress
    - Reporting
    """
    
    BANNER = """
    ██████╗ ███████╗██████╗  ██████╗██╗      █████╗ ██╗    ██╗
    ██╔══██╗██╔════╝██╔══██╗██╔════╝██║     ██╔══██╗██║    ██║
    ██████╔╝█████╗  ██║  ██║██║     ██║     ███████║██║ █╗ ██║
    ██╔══██╗██╔══╝  ██║  ██║██║     ██║     ██╔══██║██║███╗██║
    ██║  ██║███████╗██████╔╝╚██████╗███████╗██║  ██║╚███╔███╔╝
    ╚═╝  ╚═╝╚══════╝╚═════╝  ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ 
    
              Autonomous Penetration Testing System
                    Powered by Local LLM
    """
    
    def __init__(self):
        self.console = Console()
        
        # Core components
        self.llm: Optional[RedClawLLM] = None
        self.memory: Optional[MemoryManager] = None
        self.rag: Optional[RAGSystem] = None
        self.state_machine: Optional[StateMachine] = None
        
        # Agents
        self.recon_agent: Optional[ReconAgent] = None
        self.scanning_agent: Optional[ScanningAgent] = None
        self.exploit_agent: Optional[ExploitationAgent] = None
        self.post_exploit_agent: Optional[PostExploitationAgent] = None
        self.reporting_agent: Optional[ReportingAgent] = None
        
        # Tools
        self.executor: Optional[ToolExecutor] = None
        
        # Session state
        self.session_id: Optional[str] = None
        self.target: Optional[str] = None
        self.connected = False
    
    def show_banner(self):
        """Display banner"""
        self.console.print(self.BANNER, style="bold red")
        self.console.print("=" * 60, style="dim")
        self.console.print(
            f"  Version: 0.1.0 | Session: {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            style="dim"
        )
        self.console.print("=" * 60, style="dim")
        self.console.print()
    
    def print(self, message: str, style: str = None):
        """Print with optional style"""
        self.console.print(message, style=style)
    
    def print_error(self, message: str):
        """Print error message"""
        self.console.print(f"[red]✗ Error:[/red] {message}")
    
    def print_success(self, message: str):
        """Print success message"""
        self.console.print(f"[green]✓[/green] {message}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        self.console.print(f"[yellow]⚠[/yellow] {message}")
    
    def connect_llm(self) -> bool:
        """Connect to LLM API"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Connecting to LLM API...", total=None)
            
            try:
                self.llm = get_llm_client()
                health = self.llm.health_check()
                
                if health.get("status") == "healthy":
                    self.print_success(
                        f"Connected to LLM: {health.get('model', 'unknown')} "
                        f"({health.get('backend', 'unknown')})"
                    )
                    self.connected = True
                    return True
                else:
                    self.print_error(f"LLM unhealthy: {health}")
                    return False
                    
            except Exception as e:
                self.print_error(f"LLM connection failed: {e}")
                return False
    
    def init_components(self):
        """Initialize all components"""
        self.memory = get_memory_manager()
        self.rag = get_rag_system()
        self.state_machine = StateMachine()
        self.executor = ToolExecutor()
        
        # Add state machine callback
        self.state_machine.add_callback(
            lambda event, data: self.print(f"[dim][{event}] {data}[/dim]")
        )
        
        self.print_success("Components initialized")
    
    def init_agents(self):
        """Initialize all agents"""
        if not self.llm or not self.executor:
            self.print_error("LLM and executor required first")
            return
        
        self.recon_agent = ReconAgent(self.llm, self.executor)
        self.scanning_agent = ScanningAgent(self.llm, self.executor)
        self.exploit_agent = ExploitationAgent(self.llm, self.executor)
        self.post_exploit_agent = PostExploitationAgent(self.llm, self.executor)
        self.reporting_agent = ReportingAgent(self.llm)
        
        self.print_success("Agents initialized: Recon, Scanning, Exploitation, PostExploit, Reporting")
    
    def start_session(self, target: str):
        """Start new pentest session"""
        self.target = target
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize state machine
        self.state_machine = StateMachine(self.session_id)
        
        # Set reporting target
        if self.reporting_agent:
            self.reporting_agent.set_target(target)
        
        # Add to memory
        self.memory.add_to_memory(
            "session_start",
            f"Started session for target: {target}",
            {"target": target, "session_id": self.session_id}
        )
        
        self.print_success(f"Session started: {self.session_id}")
        self.print(f"Target: [bold]{target}[/bold]")
    
    async def run_recon(self):
        """Run reconnaissance phase"""
        if not self.target:
            self.print_error("No target set. Use 'target <host>'")
            return
        
        self.state_machine.transition(Phase.RECONNAISSANCE, "Starting reconnaissance")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"Reconnaissance on {self.target}...", total=None)
            
            result = await self.recon_agent.run_full_recon(self.target)
            
            # Add to memory
            self.memory.add_to_memory(
                "recon_result",
                str(result),
                {"phase": "recon", "target": self.target}
            )
            
            # Record in state machine
            self.state_machine.record_action(
                "recon",
                f"Full reconnaissance on {self.target}",
                ActionResult.SUCCESS,
                str(result)[:500]
            )
        
        # Display results
        self.print("\n[bold cyan]Reconnaissance Results[/bold cyan]")
        
        if result.get("results"):
            table = Table(title="Findings")
            table.add_column("Type", style="cyan")
            table.add_column("Source", style="green")
            table.add_column("Data", style="white")
            
            for r in result["results"]:
                data_str = str(r.get("data", {}))[:100]
                table.add_row(r.get("type", ""), r.get("source", ""), data_str)
            
            self.console.print(table)
        
        if result.get("analysis"):
            self.print("\n[bold]LLM Analysis:[/bold]")
            self.console.print(Markdown(result["analysis"]))
    
    async def run_scan(self, ports: str = "1-1000"):
        """Run scanning phase"""
        if not self.target:
            self.print_error("No target set")
            return
        
        self.state_machine.transition(Phase.SCANNING, "Starting scanning")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"Scanning {self.target}...", total=None)
            
            result = await self.scanning_agent.run_full_scan(
                self.target,
                ports=ports,
                include_vuln=True
            )
            
            self.memory.add_to_memory(
                "scan_result",
                str(result),
                {"phase": "scan", "target": self.target}
            )
            
            self.state_machine.record_action(
                "scan",
                f"Port scan on {self.target}",
                ActionResult.SUCCESS
            )
        
        # Display results
        self.print("\n[bold cyan]Scan Results[/bold cyan]")
        
        if result.get("services"):
            table = Table(title="Services Discovered")
            table.add_column("Port", style="cyan")
            table.add_column("Protocol", style="green")
            table.add_column("Service", style="white")
            table.add_column("State", style="yellow")
            
            for svc in result["services"]:
                table.add_row(
                    str(svc.get("port", "")),
                    svc.get("protocol", ""),
                    svc.get("service", ""),
                    svc.get("state", "")
                )
            
            self.console.print(table)
        
        if result.get("analysis"):
            self.print("\n[bold]Analysis:[/bold]")
            self.console.print(Markdown(result["analysis"]))
    
    async def analyze_exploits(self):
        """Analyze exploitation options"""
        if not self.scanning_agent or not self.scanning_agent.services:
            self.print_error("Run scanning first")
            return
        
        services = [
            {"port": s.port, "service": s.service, "protocol": s.protocol}
            for s in self.scanning_agent.services
        ]
        
        result = await self.exploit_agent.run_exploit_analysis(
            self.target,
            services
        )
        
        # Display
        self.print("\n[bold cyan]Exploitation Analysis[/bold cyan]")
        
        if result.get("exploits"):
            table = Table(title="Available Exploits")
            table.add_column("Name", style="cyan")
            table.add_column("CVE", style="green")
            table.add_column("Type", style="yellow")
            table.add_column("Risk", style="red")
            
            for exp in result["exploits"]:
                table.add_row(
                    exp.get("name", "")[:50],
                    exp.get("cve", "N/A"),
                    exp.get("type", ""),
                    exp.get("risk", "")
                )
            
            self.console.print(table)
        
        if result.get("analysis"):
            self.print("\n[bold]Recommended Strategy:[/bold]")
            self.console.print(Markdown(result["analysis"]))
        
        self.print_warning("Exploitation requires explicit confirmation")
    
    def generate_report(self, output_dir: str = "./reports"):
        """Generate report"""
        if not self.reporting_agent:
            self.print_error("Reporting agent not initialized")
            return
        
        # Add findings from agents
        if self.scanning_agent and self.scanning_agent.services:
            for svc in self.scanning_agent.services:
                self.reporting_agent.add_evidence(
                    "scanning",
                    f"Port {svc.port}/{svc.protocol}",
                    f"Discovered {svc.service}",
                    f"State: {svc.state}"
                )
        
        # Generate report
        filepath = self.reporting_agent.save_report(output_dir, "markdown")
        
        self.print_success(f"Report saved: {filepath}")
    
    def chat(self, message: str):
        """Direct chat with LLM"""
        if not self.llm:
            self.print_error("Not connected to LLM")
            return
        
        from ..core.llm_client import Message
        
        # Get RAG context if target is set
        context = ""
        if self.target and self.rag:
            context = self.rag.get_context_for_service(self.target)
        
        messages = [
            Message(
                role="system",
                content=f"You are RedClaw, a penetration testing assistant. "
                        f"Current target: {self.target or 'none'}. "
                        f"Context: {context[:500]}"
            ),
            Message(role="user", content=message)
        ]
        
        response = self.llm.chat(messages)
        
        self.print("\n[bold cyan]RedClaw:[/bold cyan]")
        self.console.print(Markdown(response.content))
    
    def show_status(self):
        """Show current status"""
        table = Table(title="RedClaw Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        
        table.add_row("LLM Connection", "✓ Connected" if self.connected else "✗ Disconnected")
        table.add_row("Target", self.target or "Not set")
        table.add_row("Session", self.session_id or "None")
        table.add_row("Current Phase", self.state_machine.current_phase.value if self.state_machine else "N/A")
        table.add_row("Recon Agent", "✓" if self.recon_agent else "✗")
        table.add_row("Scan Agent", "✓" if self.scanning_agent else "✗")
        table.add_row("Exploit Agent", "✓" if self.exploit_agent else "✗")
        
        self.console.print(table)
    
    def show_help(self):
        """Show help"""
        help_text = """
[bold cyan]RedClaw Commands[/bold cyan]

[bold]Setup:[/bold]
  connect       - Connect to LLM API
  target <host> - Set target for testing
  status        - Show current status

[bold]Phases:[/bold]
  recon         - Run reconnaissance
  scan [ports]  - Run port scanning (default: 1-1000)
  exploit       - Analyze exploitation options
  
[bold]Interaction:[/bold]
  chat <msg>    - Chat with RedClaw LLM
  report        - Generate report
  
[bold]Session:[/bold]
  save          - Save current session
  load <file>   - Load session from file
  
[bold]Other:[/bold]
  help          - Show this help
  clear         - Clear screen
  exit          - Exit RedClaw
"""
        self.console.print(help_text)
    
    async def interactive_loop(self):
        """Main interactive loop"""
        self.show_banner()
        
        # Auto-connect
        if not self.connect_llm():
            self.print_warning("Continue without LLM? Some features disabled.")
        else:
            self.init_components()
            self.init_agents()
        
        self.print("\nType [bold]help[/bold] for commands\n")
        
        while True:
            try:
                prompt = f"[bold red]redclaw[/bold red]"
                if self.target:
                    prompt += f"[dim]({self.target})[/dim]"
                prompt += "> "
                
                cmd = Prompt.ask(prompt)
                
                if not cmd.strip():
                    continue
                
                parts = cmd.strip().split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                # Handle commands
                if command == "exit" or command == "quit":
                    if Confirm.ask("Exit RedClaw?"):
                        break
                
                elif command == "help":
                    self.show_help()
                
                elif command == "clear":
                    self.console.clear()
                    self.show_banner()
                
                elif command == "connect":
                    if self.connect_llm():
                        self.init_components()
                        self.init_agents()
                
                elif command == "target":
                    if args:
                        self.start_session(args)
                    else:
                        self.print_error("Usage: target <hostname/IP>")
                
                elif command == "status":
                    self.show_status()
                
                elif command == "recon":
                    await self.run_recon()
                
                elif command == "scan":
                    ports = args if args else "1-1000"
                    await self.run_scan(ports)
                
                elif command == "exploit":
                    await self.analyze_exploits()
                
                elif command == "chat":
                    if args:
                        self.chat(args)
                    else:
                        self.print_error("Usage: chat <message>")
                
                elif command == "report":
                    self.generate_report()
                
                elif command == "save":
                    if self.state_machine:
                        path = f"./data/session_{self.session_id}.json"
                        self.state_machine.save_state(path)
                        self.print_success(f"Session saved: {path}")
                
                else:
                    self.print_error(f"Unknown command: {command}")
                    self.print("Type 'help' for available commands")
                
            except KeyboardInterrupt:
                self.print("\nUse 'exit' to quit")
            except Exception as e:
                self.print_error(str(e))


def main():
    """Entry point"""
    cli = RedClawCLI()
    asyncio.run(cli.interactive_loop())


if __name__ == "__main__":
    main()
