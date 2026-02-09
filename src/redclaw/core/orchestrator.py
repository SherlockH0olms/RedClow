"""
RedClaw - Agent Orchestrator
Coordinates the autonomous penetration testing workflow
"""

import asyncio
from enum import Enum
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

from .llm_client import RedClawLLM, Message, get_llm_client


class Phase(Enum):
    """Penetration testing phases"""
    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"  
    ENUMERATION = "enumeration"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    REPORTING = "reporting"
    COMPLETED = "completed"


@dataclass
class Target:
    """Target information"""
    host: str
    port_range: str = "1-1000"
    scope: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Finding:
    """Security finding"""
    phase: Phase
    severity: str  # critical, high, medium, low, info
    title: str
    description: str
    evidence: str
    remediation: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentState:
    """Current state of the agent"""
    phase: Phase = Phase.RECONNAISSANCE
    target: Optional[Target] = None
    findings: List[Finding] = field(default_factory=list)
    tool_outputs: Dict[str, str] = field(default_factory=dict)
    context_memory: List[str] = field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 50


class AgentOrchestrator:
    """
    Main orchestrator for RedClaw autonomous penetration testing.
    Coordinates phases, tool execution, and LLM reasoning.
    """
    
    PHASE_PROMPTS = {
        Phase.RECONNAISSANCE: """You are conducting reconnaissance on target: {target}.
Gather information about the target including:
- DNS information
- WHOIS data
- Subdomain enumeration
- Technology stack detection

Current context: {context}

What reconnaissance actions should be taken? Provide specific tool commands.""",

        Phase.SCANNING: """You are scanning target: {target}.
Previous reconnaissance findings: {context}

Perform port scanning and service detection:
- Identify open ports
- Detect running services
- OS fingerprinting

Provide specific nmap or masscan commands to run.""",

        Phase.ENUMERATION: """You are enumerating services on target: {target}.
Open ports and services: {context}

For each service found, enumerate:
- Version information
- Default credentials
- Known vulnerabilities
- Configuration issues

Provide specific enumeration commands.""",

        Phase.EXPLOITATION: """You are analyzing exploitation options for target: {target}.
Enumeration results: {context}

Identify potential exploits:
- Match CVEs to discovered versions
- Check for default credentials
- Identify misconfigurations

Provide exploitation recommendations (DO NOT execute without confirmation).""",

        Phase.POST_EXPLOITATION: """Post-exploitation phase for target: {target}.
Successful exploit: {context}

Perform post-exploitation:
- Privilege escalation
- Credential harvesting  
- Persistence mechanisms
- Lateral movement opportunities

Provide specific commands for post-exploitation.""",

        Phase.REPORTING: """Generate a penetration test report for target: {target}.

Findings: {context}

Create a comprehensive report including:
- Executive summary
- Methodology
- Findings with severity ratings
- Remediation recommendations"""
    }
    
    def __init__(
        self,
        llm: Optional[RedClawLLM] = None,
        tool_executor: Optional[Callable] = None,
        auto_exploit: bool = False
    ):
        self.llm = llm or get_llm_client()
        self.tool_executor = tool_executor
        self.auto_exploit = auto_exploit
        self.state = AgentState()
        self.callbacks: List[Callable] = []
    
    def set_target(self, host: str, port_range: str = "1-1000", scope: List[str] = None):
        """Set the target for penetration testing"""
        self.state.target = Target(
            host=host,
            port_range=port_range,
            scope=scope or [host]
        )
        self.state.phase = Phase.RECONNAISSANCE
        self.state.iteration = 0
        self._log(f"Target set: {host}")
    
    def add_callback(self, callback: Callable):
        """Add a callback for state changes"""
        self.callbacks.append(callback)
    
    def _log(self, message: str):
        """Log and notify callbacks"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.state.context_memory.append(log_entry)
        
        for callback in self.callbacks:
            callback(log_entry)
    
    def _get_context(self) -> str:
        """Get current context for LLM"""
        # Last 10 context items
        recent = self.state.context_memory[-10:]
        return "\n".join(recent)
    
    async def think(self) -> str:
        """
        Use LLM to reason about next action based on current phase
        """
        if not self.state.target:
            return "No target set. Use set_target() first."
        
        prompt_template = self.PHASE_PROMPTS.get(self.state.phase, "")
        prompt = prompt_template.format(
            target=self.state.target.host,
            context=self._get_context()
        )
        
        messages = [
            Message(role="system", content="You are RedClaw, an autonomous penetration testing AI. Provide specific, actionable commands."),
            Message(role="user", content=prompt)
        ]
        
        response = self.llm.chat(messages)
        self._log(f"LLM reasoning: {response.content[:200]}...")
        
        return response.content
    
    async def execute_tool(self, command: str) -> str:
        """Execute a security tool command"""
        if self.tool_executor:
            result = await self.tool_executor(command)
        else:
            result = f"[SIMULATED] Would execute: {command}"
        
        self.state.tool_outputs[command] = result
        self._log(f"Tool executed: {command[:50]}...")
        
        return result
    
    def add_finding(
        self,
        severity: str,
        title: str,
        description: str,
        evidence: str,
        remediation: str = ""
    ):
        """Add a security finding"""
        finding = Finding(
            phase=self.state.phase,
            severity=severity,
            title=title,
            description=description,
            evidence=evidence,
            remediation=remediation
        )
        self.state.findings.append(finding)
        self._log(f"Finding added: [{severity.upper()}] {title}")
    
    def advance_phase(self):
        """Move to next phase"""
        phase_order = list(Phase)
        current_idx = phase_order.index(self.state.phase)
        
        if current_idx < len(phase_order) - 1:
            self.state.phase = phase_order[current_idx + 1]
            self._log(f"Advanced to phase: {self.state.phase.value}")
    
    async def step(self) -> Dict[str, Any]:
        """
        Execute one step of the autonomous workflow
        
        Returns:
            Dict with step results
        """
        self.state.iteration += 1
        
        if self.state.iteration > self.state.max_iterations:
            self._log("Max iterations reached")
            return {"status": "max_iterations", "phase": self.state.phase.value}
        
        if self.state.phase == Phase.COMPLETED:
            return {"status": "completed", "findings": len(self.state.findings)}
        
        # Think about next action
        reasoning = await self.think()
        
        return {
            "status": "running",
            "phase": self.state.phase.value,
            "iteration": self.state.iteration,
            "reasoning": reasoning
        }
    
    async def run(self, max_steps: int = 10) -> Dict[str, Any]:
        """
        Run the autonomous penetration test
        
        Args:
            max_steps: Maximum steps before stopping
            
        Returns:
            Final results
        """
        self._log(f"Starting autonomous pentest on {self.state.target.host}")
        
        for i in range(max_steps):
            result = await self.step()
            
            if result["status"] in ["completed", "max_iterations"]:
                break
            
            # Check for exploitation phase - require confirmation if not auto
            if self.state.phase == Phase.EXPLOITATION and not self.auto_exploit:
                self._log("Exploitation phase requires manual confirmation")
                break
        
        return {
            "target": self.state.target.host,
            "phases_completed": self.state.phase.value,
            "findings": [
                {
                    "severity": f.severity,
                    "title": f.title,
                    "description": f.description
                }
                for f in self.state.findings
            ],
            "iterations": self.state.iteration
        }
    
    def generate_report(self) -> str:
        """Generate markdown report"""
        if not self.state.target:
            return "No target set"
        
        report = f"""# RedClaw Penetration Test Report

## Target: {self.state.target.host}
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Status:** {self.state.phase.value}

## Executive Summary
Automated penetration test performed by RedClaw AI agent.
Total findings: {len(self.state.findings)}

## Findings

"""
        for finding in self.state.findings:
            report += f"""### [{finding.severity.upper()}] {finding.title}
**Phase:** {finding.phase.value}
**Description:** {finding.description}
**Evidence:** 
```
{finding.evidence}
```
**Remediation:** {finding.remediation}

---

"""
        
        return report
