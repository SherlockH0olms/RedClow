"""
RedClaw CLI - Claude Code-like TUI Application
Professional terminal UI with Rich library
"""

import asyncio
import os
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
from rich.style import Style
from rich.prompt import Prompt, Confirm
from rich import box

from ..core import (
    RedClawLLM, get_llm_client, Message, StreamChunk,
    ScenarioOrchestrator, StateMachine, Phase,
    MemoryManager, RAGSystem
)


# ==================== Styles ====================

STYLES = {
    "title": Style(color="bright_cyan", bold=True),
    "subtitle": Style(color="cyan"),
    "success": Style(color="bright_green"),
    "error": Style(color="bright_red"),
    "warning": Style(color="bright_yellow"),
    "info": Style(color="bright_blue"),
    "muted": Style(color="bright_black"),
    "highlight": Style(color="bright_magenta"),
    "target": Style(color="bright_yellow", bold=True),
}

SEVERITY_COLORS = {
    "critical": "bright_red",
    "high": "red",
    "medium": "yellow",
    "low": "bright_blue",
    "info": "bright_black"
}


# ==================== Banner ====================

BANNER = """
[bright_red]
██████╗ ███████╗██████╗  ██████╗██╗      █████╗ ██╗    ██╗
██╔══██╗██╔════╝██╔══██╗██╔════╝██║     ██╔══██╗██║    ██║
██████╔╝█████╗  ██║  ██║██║     ██║     ███████║██║ █╗ ██║
██╔══██╗██╔══╝  ██║  ██║██║     ██║     ██╔══██║██║███╗██║
██║  ██║███████╗██████╔╝╚██████╗███████╗██║  ██║╚███╔███╔╝
╚═╝  ╚═╝╚══════╝╚═════╝  ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ 
[/bright_red]
[bright_cyan]v2.0[/bright_cyan] | [bright_yellow]Autonomous Red Team AI Agent[/bright_yellow]
"""

HELP_TEXT = """
[bold cyan]Commands:[/bold cyan]
  [green]target[/green] <host>    - Set target for testing
  [green]scan[/green]             - Start reconnaissance & scanning
  [green]exploit[/green]          - Attempt exploitation (requires confirmation)
  [green]report[/green]           - Generate findings report
  
  [green]status[/green]           - Show current session status
  [green]findings[/green]         - List discovered findings
  [green]history[/green]          - Show command history
  
  [green]session save[/green]     - Save current session
  [green]session load[/green] <id>- Load previous session
  [green]session list[/green]     - List saved sessions
  
  [green]config[/green]           - Show configuration
  [green]help[/green]             - Show this help
  [green]exit[/green]             - Exit RedClaw

[bold cyan]Interactive Mode:[/bold cyan]
  Just type your request in natural language!
  Example: "Find all open ports on the target"
"""


class RedClawApp:
    """
    RedClaw CLI Application
    
    Claude Code-inspired interface with:
    - Streaming LLM responses
    - Rich panels and tables
    - Progress indicators
    - Session management
    """
    
    def __init__(
        self,
        llm_url: Optional[str] = None,
        workspace: Optional[str] = None
    ):
        self.console = Console()
        self.workspace = Path(workspace or os.getcwd())
        
        # Core components
        self.llm: Optional[RedClawLLM] = None
        self.orchestrator: Optional[ScenarioOrchestrator] = None
        self.memory: Optional[MemoryManager] = None
        self.rag: Optional[RAGSystem] = None
        
        # State
        self.target: Optional[str] = None
        self.session_id: Optional[str] = None
        self.phase = Phase.PRE_ENGAGEMENT
        self.findings: List[Dict] = []
        self.command_history: List[str] = []
        
        # Settings
        self.auto_exploit = False
        self.verbose = False
        self.llm_url = llm_url
    
    async def initialize(self) -> bool:
        """Initialize all components"""
        
        with self.console.status("[bold cyan]Initializing RedClaw...", spinner="dots"):
            try:
                # Initialize LLM
                self.llm = RedClawLLM(
                    api_url=self.llm_url or os.getenv("LLM_API_URL"),
                    model=os.getenv("LLM_MODEL", "phi-4")
                )
                
                health = self.llm.health_check()
                if health.get("status") != "healthy":
                    self.console.print(
                        f"[yellow]⚠ LLM connection: {health.get('status', 'unknown')}[/yellow]"
                    )
                
                # Initialize memory
                data_dir = self.workspace / "data"
                data_dir.mkdir(exist_ok=True)
                
                self.memory = MemoryManager(
                    persist_dir=str(data_dir / "memory")
                )
                self.session_id = self.memory.session_id
                
                # Initialize RAG
                self.rag = RAGSystem(
                    persist_dir=str(data_dir / "rag")
                )
                
                # Initialize orchestrator
                self.orchestrator = ScenarioOrchestrator(
                    llm=self.llm,
                    auto_exploit=self.auto_exploit
                )
                
                return True
                
            except Exception as e:
                self.console.print(f"[red]Initialization failed: {e}[/red]")
                return False
    
    def show_banner(self):
        """Display banner"""
        self.console.print(BANNER)
        self.console.print()
    
    def show_status(self):
        """Show current status panel"""
        
        status_table = Table(
            show_header=False,
            box=box.SIMPLE,
            padding=(0, 1)
        )
        status_table.add_column("Key", style="cyan")
        status_table.add_column("Value")
        
        status_table.add_row("Session", self.session_id or "N/A")
        status_table.add_row(
            "Target",
            f"[bright_yellow]{self.target}[/bright_yellow]" if self.target else "[dim]Not set[/dim]"
        )
        status_table.add_row("Phase", self.phase.value)
        status_table.add_row("Findings", str(len(self.findings)))
        
        if self.memory:
            stats = self.memory.get_stats()
            status_table.add_row("Memory", f"{stats.get('findings_count', 0)} entries")
        
        if self.rag:
            rag_stats = self.rag.get_stats()
            status_table.add_row(
                "Knowledge",
                f"MITRE: {rag_stats.get('mitre_count', 0)}, Exploits: {rag_stats.get('exploit_count', 0)}"
            )
        
        self.console.print(Panel(
            status_table,
            title="[bold cyan]Status[/bold cyan]",
            border_style="cyan"
        ))
    
    def show_findings(self):
        """Display findings table"""
        
        if not self.findings:
            self.console.print("[dim]No findings yet.[/dim]")
            return
        
        table = Table(
            title="Security Findings",
            box=box.ROUNDED,
            show_lines=True
        )
        
        table.add_column("#", style="dim", width=3)
        table.add_column("Severity", width=10)
        table.add_column("Type", width=15)
        table.add_column("Title", width=40)
        table.add_column("Target", width=20)
        
        for i, finding in enumerate(self.findings, 1):
            severity = finding.get("severity", "info")
            color = SEVERITY_COLORS.get(severity, "white")
            
            table.add_row(
                str(i),
                f"[{color}]{severity.upper()}[/{color}]",
                finding.get("type", "N/A"),
                finding.get("title", "N/A"),
                finding.get("target", self.target or "N/A")
            )
        
        self.console.print(table)
    
    async def stream_response(self, prompt: str) -> str:
        """Stream LLM response with live display"""
        
        messages = [
            Message(role="system", content=self.llm.SYSTEM_PROMPT),
        ]
        
        # Add context
        if self.target:
            messages.append(Message(
                role="system",
                content=f"Current target: {self.target}\nPhase: {self.phase.value}"
            ))
        
        # Add RAG context
        if self.rag and self.target:
            rag_context = self.rag.get_context_for_target(self.target)
            if rag_context:
                messages.append(Message(
                    role="system",
                    content=f"Relevant security context:\n{rag_context[:2000]}"
                ))
        
        messages.append(Message(role="user", content=prompt))
        
        full_response = ""
        
        self.console.print()
        with Live(
            Panel("", title="[bold cyan]RedClaw[/bold cyan]", border_style="cyan"),
            console=self.console,
            refresh_per_second=10
        ) as live:
            for chunk in self.llm.chat_stream(messages):
                if chunk.done:
                    break
                full_response += chunk.content
                
                # Render as markdown
                try:
                    md = Markdown(full_response)
                    live.update(Panel(
                        md,
                        title="[bold cyan]RedClaw[/bold cyan]",
                        border_style="cyan"
                    ))
                except:
                    live.update(Panel(
                        Text(full_response),
                        title="[bold cyan]RedClaw[/bold cyan]",
                        border_style="cyan"
                    ))
        
        return full_response
    
    async def handle_command(self, command: str) -> bool:
        """Handle user command, return False to exit"""
        
        command = command.strip()
        if not command:
            return True
        
        self.command_history.append(command)
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Built-in commands
        if cmd in ("exit", "quit", "q"):
            return False
        
        elif cmd == "help":
            self.console.print(Markdown(HELP_TEXT))
        
        elif cmd == "status":
            self.show_status()
        
        elif cmd == "findings":
            self.show_findings()
        
        elif cmd == "history":
            for i, h in enumerate(self.command_history[-20:], 1):
                self.console.print(f"[dim]{i}.[/dim] {h}")
        
        elif cmd == "target":
            if args:
                self.target = args
                self.phase = Phase.RECONNAISSANCE
                self.console.print(f"[green]✓[/green] Target set: [bright_yellow]{self.target}[/bright_yellow]")
            else:
                self.console.print("[yellow]Usage: target <hostname or IP>[/yellow]")
        
        elif cmd == "scan":
            if not self.target:
                self.console.print("[yellow]No target set. Use 'target <host>' first.[/yellow]")
            else:
                await self._run_scan()
        
        elif cmd == "exploit":
            if not self.target:
                self.console.print("[yellow]No target set.[/yellow]")
            elif not self.findings:
                self.console.print("[yellow]No findings to exploit. Run 'scan' first.[/yellow]")
            else:
                if Confirm.ask("[yellow]⚠ Attempt exploitation?[/yellow]"):
                    await self._run_exploit()
        
        elif cmd == "report":
            await self._generate_report()
        
        elif cmd == "config":
            self._show_config()
        
        elif cmd == "session":
            await self._handle_session(args)
        
        elif cmd == "clear":
            self.console.clear()
            self.show_banner()
        
        else:
            # Natural language query
            await self.stream_response(command)
        
        return True
    
    async def _run_scan(self):
        """Run scanning workflow"""
        
        self.console.print(f"\n[cyan]Starting scan on[/cyan] [bright_yellow]{self.target}[/bright_yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Scanning...", total=100)
            
            # Phase 1: Recon
            progress.update(task, description="Reconnaissance...")
            await asyncio.sleep(0.5)
            recon_result = await self.stream_response(
                f"Perform passive reconnaissance on {self.target}. "
                "What DNS records, WHOIS info, and technology stack can you identify?"
            )
            progress.update(task, advance=30)
            
            # Phase 2: Port scan
            progress.update(task, description="Port scanning...")
            await asyncio.sleep(0.3)
            scan_result = await self.stream_response(
                f"What nmap command would you recommend for {self.target}? "
                "Provide the exact command and explain what it does."
            )
            progress.update(task, advance=30)
            
            # Phase 3: Vulnerability assessment
            progress.update(task, description="Vulnerability assessment...")
            vuln_result = await self.stream_response(
                f"Based on typical services, what vulnerabilities should we check for on {self.target}? "
                "List specific CVEs or vulnerability classes."
            )
            progress.update(task, advance=40)
        
        # Add sample findings
        self.findings.append({
            "type": "reconnaissance",
            "title": "Reconnaissance Complete",
            "description": "Initial reconnaissance performed",
            "severity": "info",
            "target": self.target
        })
        
        self.phase = Phase.VULNERABILITY_ANALYSIS
        self.console.print(f"\n[green]✓[/green] Scan complete. {len(self.findings)} finding(s).")
    
    async def _run_exploit(self):
        """Run exploitation workflow"""
        
        self.console.print(f"\n[yellow]⚠ Attempting exploitation on[/yellow] [bright_yellow]{self.target}[/bright_yellow]")
        
        await self.stream_response(
            f"I have the following findings for {self.target}:\n"
            f"{self.findings}\n\n"
            "What exploitation techniques would you recommend? "
            "Be specific about tools and methods."
        )
        
        self.phase = Phase.POST_EXPLOITATION
    
    async def _generate_report(self):
        """Generate findings report"""
        
        self.console.print("\n[cyan]Generating report...[/cyan]")
        
        report_content = f"""# RedClaw Security Assessment Report

## Target: {self.target or 'N/A'}
## Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
## Session: {self.session_id}

## Executive Summary
Security assessment performed using RedClaw autonomous red team agent.

## Findings ({len(self.findings)})
"""
        for i, f in enumerate(self.findings, 1):
            report_content += f"""
### {i}. {f.get('title', 'Finding')}
- **Severity**: {f.get('severity', 'N/A').upper()}
- **Type**: {f.get('type', 'N/A')}
- **Description**: {f.get('description', 'N/A')}
"""
        
        report_content += """
## Recommendations
See individual findings for specific remediation steps.

---
*Generated by RedClaw v2.0*
"""
        
        # Save report
        reports_dir = self.workspace / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / f"report_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_file.write_text(report_content)
        
        self.console.print(Markdown(report_content))
        self.console.print(f"\n[green]✓[/green] Report saved: [cyan]{report_file}[/cyan]")
        
        self.phase = Phase.REPORTING
    
    def _show_config(self):
        """Show configuration"""
        
        table = Table(title="Configuration", box=box.ROUNDED)
        table.add_column("Setting", style="cyan")
        table.add_column("Value")
        
        table.add_row("LLM URL", self.llm.api_url if self.llm else "N/A")
        table.add_row("LLM Model", self.llm.model if self.llm else "N/A")
        table.add_row("Workspace", str(self.workspace))
        table.add_row("Auto-Exploit", "Enabled" if self.auto_exploit else "Disabled")
        table.add_row("Verbose", "Yes" if self.verbose else "No")
        
        self.console.print(table)
    
    async def _handle_session(self, args: str):
        """Handle session commands"""
        
        parts = args.split()
        subcmd = parts[0] if parts else "list"
        
        if subcmd == "save":
            if self.memory:
                self.memory.save_session(
                    target=self.target or "",
                    phase=self.phase.value,
                    state={"findings": self.findings}
                )
                self.console.print(f"[green]✓[/green] Session saved: {self.session_id}")
        
        elif subcmd == "load":
            if len(parts) > 1 and self.memory:
                session_data = self.memory.load_session(parts[1])
                if session_data:
                    self.target = session_data.get("target")
                    self.phase = Phase(session_data.get("phase", "pre_engagement"))
                    self.findings = session_data.get("state", {}).get("findings", [])
                    self.console.print(f"[green]✓[/green] Session loaded")
                else:
                    self.console.print("[yellow]Session not found[/yellow]")
        
        elif subcmd == "list":
            if self.memory:
                sessions = self.memory.list_sessions()
                if sessions:
                    table = Table(title="Saved Sessions", box=box.ROUNDED)
                    table.add_column("ID", style="cyan")
                    table.add_column("Target")
                    table.add_column("Phase")
                    table.add_column("Saved")
                    
                    for s in sessions:
                        table.add_row(
                            s.get("session_id", ""),
                            s.get("target", "N/A"),
                            s.get("phase", "N/A"),
                            s.get("saved_at", "N/A")[:19]
                        )
                    
                    self.console.print(table)
                else:
                    self.console.print("[dim]No saved sessions.[/dim]")
    
    async def run(self):
        """Main application loop"""
        
        self.show_banner()
        
        if not await self.initialize():
            self.console.print("[red]Failed to initialize. Exiting.[/red]")
            return
        
        self.console.print(f"[green]✓[/green] Ready | Session: [cyan]{self.session_id}[/cyan]")
        self.console.print("[dim]Type 'help' for commands or ask anything![/dim]\n")
        
        running = True
        while running:
            try:
                # Prompt with status indicator
                phase_color = "green" if self.phase == Phase.COMPLETED else "cyan"
                target_str = f" @ {self.target}" if self.target else ""
                
                prompt = f"[bold red]RedClaw[/bold red][{phase_color}]{target_str}[/{phase_color}] > "
                
                user_input = Prompt.ask(prompt)
                running = await self.handle_command(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n[dim]Use 'exit' to quit.[/dim]")
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
        
        # Cleanup
        self.console.print("\n[cyan]Goodbye! 👋[/cyan]")
        if self.llm:
            self.llm.close()


async def main():
    """Entry point"""
    app = RedClawApp()
    await app.run()


def cli_entry():
    """CLI entry point for setup.py"""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
