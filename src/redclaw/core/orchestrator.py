"""
RedClaw Core - Scenario Orchestrator
Multi-agent workflow orchestration with LangGraph-inspired architecture
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from .llm_client import RedClawLLM, Message, get_llm_client
from .state_machine import StateMachine, Phase, ActionResult


@dataclass
class AgentTask:
    """Task for an agent to execute"""
    id: str
    type: str  # recon, scan, exploit, post_exploit, report
    target: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    status: str = "pending"
    result: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AttackPlan:
    """Generated attack plan"""
    id: str
    target: str
    phases: List[Dict]
    estimated_time: str
    risk_level: str
    created_at: datetime


@dataclass
class ScenarioState:
    """Current scenario state"""
    scenario_id: str
    target: str
    phase: Phase
    tasks: List[AgentTask] = field(default_factory=list)
    findings: List[Dict] = field(default_factory=list)
    attack_graph: Dict = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class ScenarioOrchestrator:
    """
    Scenario Orchestrator - The Brain of RedClaw
    
    Responsibilities:
    - Generate attack plans from goals
    - Coordinate multiple specialized agents
    - Manage attack graph and state
    - Make tactical decisions based on findings
    - Handle errors and adapt strategy
    
    Architecture inspired by:
    - LangGraph for workflow orchestration
    - CrewAI for multi-agent coordination
    - AutoRedTeamer for memory-guided attack selection
    """
    
    ATTACK_TACTICS = [
        "reconnaissance",
        "resource_development", 
        "initial_access",
        "execution",
        "persistence",
        "privilege_escalation",
        "defense_evasion",
        "credential_access",
        "discovery",
        "lateral_movement",
        "collection",
        "exfiltration",
        "impact"
    ]
    
    def __init__(
        self,
        llm: Optional[RedClawLLM] = None,
        auto_exploit: bool = False
    ):
        self.llm = llm or get_llm_client()
        self.auto_exploit = auto_exploit
        
        self.state_machine = StateMachine()
        self.current_state: Optional[ScenarioState] = None
        
        # Agent registry
        self.agents: Dict[str, Any] = {}
        
        # Event callbacks
        self.callbacks: List[Callable] = []
        
        # Attack knowledge (learned patterns)
        self.attack_patterns: List[Dict] = []
    
    def register_agent(self, agent_type: str, agent: Any):
        """Register a specialized agent"""
        self.agents[agent_type] = agent
    
    def add_callback(self, callback: Callable):
        """Add event callback"""
        self.callbacks.append(callback)
    
    def emit_event(self, event: str, data: Any):
        """Emit event to callbacks"""
        for callback in self.callbacks:
            try:
                callback(event, data)
            except:
                pass
    
    async def create_scenario(
        self,
        goal: str,
        target: str,
        scope: Optional[List[str]] = None
    ) -> ScenarioState:
        """Create new attack scenario from goal"""
        
        scenario_id = str(uuid.uuid4())[:8]
        
        self.emit_event("scenario_created", {
            "id": scenario_id,
            "goal": goal,
            "target": target
        })
        
        # Generate attack plan via LLM
        plan = await self._generate_attack_plan(goal, target, scope)
        
        # Initialize state
        self.current_state = ScenarioState(
            scenario_id=scenario_id,
            target=target,
            phase=Phase.PRE_ENGAGEMENT,
            attack_graph={"nodes": [], "edges": []}
        )
        
        # Convert plan to tasks
        for phase_info in plan.phases:
            task = AgentTask(
                id=str(uuid.uuid4())[:8],
                type=phase_info["type"],
                target=target,
                parameters=phase_info.get("parameters", {}),
                priority=phase_info.get("priority", 0)
            )
            self.current_state.tasks.append(task)
        
        return self.current_state
    
    async def _generate_attack_plan(
        self,
        goal: str,
        target: str,
        scope: Optional[List[str]] = None
    ) -> AttackPlan:
        """Use LLM to generate attack plan"""
        
        prompt = f"""Generate a detailed attack plan for the following scenario:

Goal: {goal}
Target: {target}
Scope: {scope or 'Full penetration test'}

Return a JSON object with this structure:
{{
    "phases": [
        {{
            "type": "recon|scan|exploit|post_exploit|report",
            "name": "Phase name",
            "description": "What to do",
            "tools": ["tool1", "tool2"],
            "parameters": {{}},
            "priority": 0-10,
            "estimated_time": "X minutes"
        }}
    ],
    "estimated_total_time": "X hours",
    "risk_level": "low|medium|high|critical"
}}

Include at minimum:
1. Passive reconnaissance
2. Active scanning
3. Vulnerability assessment
4. Exploitation attempts (if authorized)
5. Report generation
"""
        
        messages = [
            Message(role="system", content="You are a penetration testing planner. Output valid JSON only."),
            Message(role="user", content=prompt)
        ]
        
        response = await self.llm.achat(messages, max_tokens=4096)
        
        try:
            # Extract JSON from response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            plan_data = json.loads(content.strip())
            
            return AttackPlan(
                id=str(uuid.uuid4())[:8],
                target=target,
                phases=plan_data.get("phases", []),
                estimated_time=plan_data.get("estimated_total_time", "unknown"),
                risk_level=plan_data.get("risk_level", "medium"),
                created_at=datetime.now()
            )
        except json.JSONDecodeError:
            # Fallback to default plan
            return self._default_attack_plan(target)
    
    def _default_attack_plan(self, target: str) -> AttackPlan:
        """Default attack plan when LLM fails"""
        return AttackPlan(
            id=str(uuid.uuid4())[:8],
            target=target,
            phases=[
                {
                    "type": "recon",
                    "name": "Reconnaissance",
                    "description": "Gather information about target",
                    "tools": ["whois", "dig", "nslookup"],
                    "priority": 10
                },
                {
                    "type": "scan",
                    "name": "Port Scanning",
                    "description": "Identify open ports and services",
                    "tools": ["nmap"],
                    "parameters": {"ports": "1-10000"},
                    "priority": 9
                },
                {
                    "type": "scan",
                    "name": "Vulnerability Scan",
                    "description": "Scan for known vulnerabilities",
                    "tools": ["nuclei", "nikto"],
                    "priority": 8
                },
                {
                    "type": "exploit",
                    "name": "Exploitation",
                    "description": "Attempt to exploit vulnerabilities",
                    "tools": ["searchsploit", "metasploit"],
                    "priority": 5
                },
                {
                    "type": "report",
                    "name": "Reporting",
                    "description": "Generate findings report",
                    "tools": [],
                    "priority": 1
                }
            ],
            estimated_time="2-4 hours",
            risk_level="medium",
            created_at=datetime.now()
        )
    
    async def execute_scenario(
        self,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """Execute the current scenario"""
        
        if not self.current_state:
            raise ValueError("No scenario created")
        
        results = {
            "scenario_id": self.current_state.scenario_id,
            "target": self.current_state.target,
            "phases": [],
            "findings": [],
            "success": True
        }
        
        # Sort tasks by priority
        tasks = sorted(self.current_state.tasks, key=lambda t: -t.priority)
        
        for task in tasks:
            self.emit_event("task_started", {"task_id": task.id, "type": task.type})
            
            if progress_callback:
                progress_callback(f"Executing: {task.type}")
            
            try:
                # Execute based on task type
                if task.type == "recon":
                    result = await self._execute_recon(task)
                elif task.type == "scan":
                    result = await self._execute_scan(task)
                elif task.type == "exploit":
                    result = await self._execute_exploit(task)
                elif task.type == "post_exploit":
                    result = await self._execute_post_exploit(task)
                elif task.type == "report":
                    result = await self._execute_report(task)
                else:
                    result = {"error": f"Unknown task type: {task.type}"}
                
                task.status = "completed"
                task.result = result
                results["phases"].append({
                    "type": task.type,
                    "status": "success",
                    "result": result
                })
                
                # Update attack graph
                self._update_attack_graph(task, result)
                
                # Analyze results and adjust strategy
                await self._analyze_and_adapt(task, result)
                
            except Exception as e:
                task.status = "failed"
                task.result = {"error": str(e)}
                results["phases"].append({
                    "type": task.type,
                    "status": "failed",
                    "error": str(e)
                })
            
            self.emit_event("task_completed", {
                "task_id": task.id,
                "status": task.status
            })
        
        # Compile findings
        results["findings"] = self.current_state.findings
        self.current_state.completed_at = datetime.now()
        
        return results
    
    async def _execute_recon(self, task: AgentTask) -> Dict:
        """Execute reconnaissance task"""
        if "recon" in self.agents:
            return await self.agents["recon"].run(
                task.target,
                **task.parameters
            )
        
        # Fallback: use LLM to plan recon
        prompt = f"""Plan reconnaissance for target: {task.target}

Specify exact commands to gather:
- WHOIS information
- DNS records
- Subdomains
- Technology stack

Return as JSON with commands array."""
        
        messages = [
            Message(role="system", content="You are a reconnaissance specialist."),
            Message(role="user", content=prompt)
        ]
        
        response = await self.llm.achat(messages)
        return {"plan": response.content, "status": "planned"}
    
    async def _execute_scan(self, task: AgentTask) -> Dict:
        """Execute scanning task"""
        if "scan" in self.agents:
            return await self.agents["scan"].run(
                task.target,
                **task.parameters
            )
        
        return {"status": "planned", "target": task.target}
    
    async def _execute_exploit(self, task: AgentTask) -> Dict:
        """Execute exploitation task"""
        if not self.auto_exploit:
            return {
                "status": "skipped",
                "reason": "Auto-exploit disabled. Manual confirmation required."
            }
        
        if "exploit" in self.agents:
            return await self.agents["exploit"].run(
                task.target,
                **task.parameters
            )
        
        return {"status": "planned", "target": task.target}
    
    async def _execute_post_exploit(self, task: AgentTask) -> Dict:
        """Execute post-exploitation task"""
        if "post_exploit" in self.agents:
            return await self.agents["post_exploit"].run(
                task.target,
                **task.parameters
            )
        
        return {"status": "planned", "target": task.target}
    
    async def _execute_report(self, task: AgentTask) -> Dict:
        """Execute reporting task"""
        if "report" in self.agents:
            return await self.agents["report"].generate(
                self.current_state.findings,
                **task.parameters
            )
        
        return {
            "status": "completed",
            "findings_count": len(self.current_state.findings)
        }
    
    def _update_attack_graph(self, task: AgentTask, result: Dict):
        """Update attack graph with new node/edges"""
        if not self.current_state:
            return
        
        node = {
            "id": task.id,
            "type": task.type,
            "target": task.target,
            "status": task.status,
            "timestamp": datetime.now().isoformat()
        }
        
        self.current_state.attack_graph["nodes"].append(node)
        
        # Add edge from previous node
        nodes = self.current_state.attack_graph["nodes"]
        if len(nodes) > 1:
            edge = {
                "source": nodes[-2]["id"],
                "target": node["id"],
                "label": task.type
            }
            self.current_state.attack_graph["edges"].append(edge)
    
    async def _analyze_and_adapt(self, task: AgentTask, result: Dict):
        """Analyze results and adapt strategy"""
        
        # Check for findings
        findings = result.get("findings", [])
        if findings:
            self.current_state.findings.extend(findings)
        
        # Check for vulnerabilities that need immediate action
        vulns = result.get("vulnerabilities", [])
        critical_vulns = [v for v in vulns if v.get("severity") == "critical"]
        
        if critical_vulns and not self.auto_exploit:
            self.emit_event("critical_vuln_found", {
                "count": len(critical_vulns),
                "vulns": critical_vulns[:3]  # First 3
            })
    
    def get_state(self) -> Optional[ScenarioState]:
        """Get current scenario state"""
        return self.current_state
    
    def get_attack_graph(self) -> Dict:
        """Get attack graph for visualization"""
        if not self.current_state:
            return {"nodes": [], "edges": []}
        return self.current_state.attack_graph
    
    async def interactive_step(self, user_input: str) -> str:
        """Process user input in interactive mode"""
        
        context = ""
        if self.current_state:
            context = f"""
Current target: {self.current_state.target}
Phase: {self.current_state.phase.value}
Findings: {len(self.current_state.findings)}
Tasks: {len(self.current_state.tasks)}
"""
        
        messages = [
            Message(role="system", content=self.llm.SYSTEM_PROMPT),
            Message(role="user", content=f"{context}\n\nUser request: {user_input}")
        ]
        
        response = await self.llm.achat(messages)
        return response.content
