"""
RedClaw Agents - Base Agent
Abstract base class for all specialized security agents
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from ..core.llm_client import RedClawLLM, Message, get_llm_client
from ..core.memory import MemoryManager
from ..core.rag import RAGSystem


class AgentState(Enum):
    """Agent execution state"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    ERROR = "error"


class AgentCapability(Enum):
    """Agent capabilities"""
    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    LATERAL_MOVEMENT = "lateral_movement"
    PERSISTENCE = "persistence"
    CREDENTIAL_ACCESS = "credential_access"
    REPORTING = "reporting"


@dataclass
class AgentResult:
    """Result from agent execution"""
    success: bool
    data: Dict = field(default_factory=dict)
    findings: List[Dict] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    error: Optional[str] = None
    duration: float = 0.0
    next_actions: List[str] = field(default_factory=list)


@dataclass
class ToolCall:
    """Tool call request from agent"""
    tool: str
    args: Dict
    reason: str


class BaseAgent(ABC):
    """
    Base Agent for RedClaw
    
    All specialized agents (recon, scan, exploit, etc.) inherit from this.
    
    Features:
    - LLM-powered reasoning
    - RAG context injection
    - Tool execution
    - State management
    - Result collection
    """
    
    # Agent metadata (override in subclasses)
    AGENT_TYPE = "base"
    AGENT_NAME = "Base Agent"
    AGENT_DESCRIPTION = "Abstract base agent"
    
    SUPPORTED_TOOLS: List[str] = []
    
    def __init__(
        self,
        llm: Optional[RedClawLLM] = None,
        memory: Optional[MemoryManager] = None,
        rag: Optional[RAGSystem] = None,
        tools_executor: Optional[Callable] = None
    ):
        self.llm = llm or get_llm_client()
        self.memory = memory
        self.rag = rag
        self.tools_executor = tools_executor
        
        self.state = AgentState.IDLE
        self.current_target: Optional[str] = None
        self.findings: List[Dict] = []
        self.artifacts: List[str] = []
        
        # Event callbacks
        self.callbacks: List[Callable] = []
    
    def add_callback(self, callback: Callable):
        """Add event callback"""
        self.callbacks.append(callback)
    
    def emit_event(self, event: str, data: Any = None):
        """Emit event to callbacks"""
        for cb in self.callbacks:
            try:
                cb(self.AGENT_TYPE, event, data)
            except:
                pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get agent-specific system prompt"""
        pass
    
    @abstractmethod
    async def plan(self, target: str, context: Dict = None) -> List[ToolCall]:
        """Plan actions for target"""
        pass
    
    @abstractmethod
    async def analyze_results(self, results: List[Dict]) -> Dict:
        """Analyze execution results"""
        pass
    
    async def run(
        self,
        target: str,
        context: Optional[Dict] = None,
        **kwargs
    ) -> AgentResult:
        """
        Execute agent workflow
        
        1. Plan actions using LLM
        2. Execute tools
        3. Analyze results
        4. Return findings
        """
        
        start_time = datetime.now()
        self.current_target = target
        self.findings = []
        self.artifacts = []
        
        try:
            # Phase 1: Planning
            self.state = AgentState.PLANNING
            self.emit_event("planning", {"target": target})
            
            # Get RAG context if available
            rag_context = ""
            if self.rag:
                rag_context = self.rag.get_context_for_target(
                    target,
                    context.get("technologies", []) if context else []
                )
            
            plan_context = {
                **(context or {}),
                "rag_context": rag_context
            }
            
            tool_calls = await self.plan(target, plan_context)
            
            if not tool_calls:
                return AgentResult(
                    success=True,
                    data={"message": "No actions needed"},
                    duration=self._calc_duration(start_time)
                )
            
            # Phase 2: Execution
            self.state = AgentState.EXECUTING
            self.emit_event("executing", {"tool_count": len(tool_calls)})
            
            execution_results = []
            for tool_call in tool_calls:
                self.emit_event("tool_start", {"tool": tool_call.tool})
                
                result = await self._execute_tool(tool_call)
                execution_results.append({
                    "tool": tool_call.tool,
                    "args": tool_call.args,
                    "result": result
                })
                
                self.emit_event("tool_complete", {
                    "tool": tool_call.tool,
                    "success": result.get("success", True)
                })
            
            # Phase 3: Analysis
            self.state = AgentState.ANALYZING
            self.emit_event("analyzing", {"results_count": len(execution_results)})
            
            analysis = await self.analyze_results(execution_results)
            
            # Extract findings
            self.findings = analysis.get("findings", [])
            
            # Store findings in memory
            if self.memory:
                for finding in self.findings:
                    self.memory.add_finding(
                        finding_type=finding.get("type", "general"),
                        title=finding.get("title", "Finding"),
                        description=finding.get("description", ""),
                        severity=finding.get("severity", "info"),
                        target=target
                    )
            
            # Complete
            self.state = AgentState.COMPLETED
            self.emit_event("completed", {"findings_count": len(self.findings)})
            
            return AgentResult(
                success=True,
                data=analysis,
                findings=self.findings,
                artifacts=self.artifacts,
                duration=self._calc_duration(start_time),
                next_actions=analysis.get("next_actions", [])
            )
            
        except Exception as e:
            self.state = AgentState.ERROR
            self.emit_event("error", {"error": str(e)})
            
            return AgentResult(
                success=False,
                error=str(e),
                duration=self._calc_duration(start_time)
            )
    
    async def _execute_tool(self, tool_call: ToolCall) -> Dict:
        """Execute a single tool"""
        if self.tools_executor:
            try:
                return await self.tools_executor(tool_call.tool, tool_call.args)
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Default: return planned action (no actual execution)
        return {
            "success": True,
            "status": "planned",
            "tool": tool_call.tool,
            "args": tool_call.args
        }
    
    def _calc_duration(self, start_time: datetime) -> float:
        """Calculate duration in seconds"""
        return (datetime.now() - start_time).total_seconds()
    
    async def _llm_plan(
        self,
        target: str,
        task: str,
        context: str = ""
    ) -> List[ToolCall]:
        """Use LLM to plan actions"""
        
        prompt = f"""Plan security testing actions for:
Target: {target}
Task: {task}

{f"Context:{chr(10)}{context}" if context else ""}

Available tools: {', '.join(self.SUPPORTED_TOOLS)}

Return a JSON array of tool calls:
[
    {{"tool": "tool_name", "args": {{}}, "reason": "why this tool"}}
]

Be specific with arguments. Only use available tools."""
        
        messages = [
            Message(role="system", content=self.get_system_prompt()),
            Message(role="user", content=prompt)
        ]
        
        response = await self.llm.achat(messages, max_tokens=2048)
        
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            calls_data = json.loads(content.strip())
            
            return [
                ToolCall(
                    tool=c["tool"],
                    args=c.get("args", {}),
                    reason=c.get("reason", "")
                )
                for c in calls_data
                if c.get("tool") in self.SUPPORTED_TOOLS
            ]
        except:
            return []
    
    async def _llm_analyze(
        self,
        results: List[Dict],
        analysis_prompt: str
    ) -> Dict:
        """Use LLM to analyze results"""
        
        prompt = f"""{analysis_prompt}

Results:
{json.dumps(results, indent=2, default=str)}

Return JSON with:
{{
    "summary": "overall summary",
    "findings": [
        {{"type": "vuln|info|warning", "title": "...", "description": "...", "severity": "critical|high|medium|low|info"}}
    ],
    "next_actions": ["action1", "action2"],
    "risk_level": "critical|high|medium|low"
}}"""
        
        messages = [
            Message(role="system", content=self.get_system_prompt()),
            Message(role="user", content=prompt)
        ]
        
        response = await self.llm.achat(messages, max_tokens=4096)
        
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content.strip())
        except:
            return {
                "summary": "Analysis failed",
                "findings": [],
                "next_actions": [],
                "risk_level": "unknown"
            }
    
    def to_dict(self) -> Dict:
        """Export agent info as dict"""
        return {
            "type": self.AGENT_TYPE,
            "name": self.AGENT_NAME,
            "description": self.AGENT_DESCRIPTION,
            "state": self.state.value,
            "target": self.current_target,
            "findings_count": len(self.findings),
            "supported_tools": self.SUPPORTED_TOOLS
        }
