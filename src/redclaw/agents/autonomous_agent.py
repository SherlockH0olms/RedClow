"""
RedClaw Autonomous Agent - LangGraph-based ReAct Agent
This is the core AI brain that plans, executes, and analyzes penetration tests autonomously.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re

# LangGraph imports (with fallback)
try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from ..core.llm_client import RedClawLLM, get_llm_client, Message
from ..core.memory import MemoryManager
from ..tools.executor import ToolExecutor, ToolResult

# Optional LLM manager for enhanced backend support
try:
    from ..core.llm_manager import get_llm_manager, LLMManager
    LLM_MANAGER_AVAILABLE = True
except ImportError:
    LLM_MANAGER_AVAILABLE = False


class AgentPhase(Enum):
    """Current phase of the autonomous agent"""
    IDLE = "idle"
    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"
    ENUMERATION = "enumeration"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    REPORTING = "reporting"
    COMPLETED = "completed"


@dataclass
class AgentState:
    """State object passed through the agent graph"""
    target: str = ""
    objective: str = ""
    phase: AgentPhase = AgentPhase.IDLE
    
    # Gathered information
    discovered_ports: List[Dict] = field(default_factory=list)
    discovered_services: List[Dict] = field(default_factory=list)
    discovered_vulns: List[Dict] = field(default_factory=list)
    credentials: List[Dict] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    
    # Execution tracking
    tool_history: List[Dict] = field(default_factory=list)
    current_plan: List[str] = field(default_factory=list)
    completed_steps: List[str] = field(default_factory=list)
    
    # Messages for LLM
    messages: List[Dict] = field(default_factory=list)
    
    # Status
    error: Optional[str] = None
    iteration: int = 0
    max_iterations: int = 50


# Tool definitions for LLM function calling
TOOL_DEFINITIONS = [
    {
        "name": "nmap_scan",
        "description": "Scan a target for open ports and services using nmap",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target IP or hostname"},
                "ports": {"type": "string", "description": "Port range (e.g., '1-1000', '22,80,443')"},
                "scan_type": {
                    "type": "string",
                    "enum": ["quick", "default", "full", "stealth", "vuln", "udp"],
                    "description": "Type of scan to perform"
                }
            },
            "required": ["target"]
        }
    },
    {
        "name": "gobuster_scan",
        "description": "Enumerate web directories and files using gobuster",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Target URL (e.g., http://10.10.10.1)"},
                "wordlist": {"type": "string", "description": "Wordlist to use"},
                "extensions": {"type": "string", "description": "File extensions (e.g., 'php,html,txt')"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "curl_request",
        "description": "Make HTTP request to a URL",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Target URL"},
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                "data": {"type": "string", "description": "POST data"},
                "headers": {"type": "object", "description": "Custom headers"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "nikto_scan",
        "description": "Scan web server for vulnerabilities using nikto",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target URL or IP"},
                "port": {"type": "integer", "description": "Port number"}
            },
            "required": ["target"]
        }
    },
    {
        "name": "ssh_connect",
        "description": "Attempt SSH connection with credentials",
        "parameters": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "Target host"},
                "username": {"type": "string", "description": "Username"},
                "password": {"type": "string", "description": "Password"},
                "command": {"type": "string", "description": "Command to execute"}
            },
            "required": ["host", "username"]
        }
    },
    {
        "name": "ftp_connect",
        "description": "Attempt FTP connection and list/download files",
        "parameters": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "Target host"},
                "username": {"type": "string", "description": "Username (default: anonymous)"},
                "password": {"type": "string", "description": "Password"}
            },
            "required": ["host"]
        }
    },
    {
        "name": "read_file",
        "description": "Read contents of a file from the target (if accessible)",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
                "method": {"type": "string", "enum": ["cat", "curl", "wget"]}
            },
            "required": ["path"]
        }
    },
    {
        "name": "bash_command",
        "description": "Execute a bash command on the attack machine",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Bash command to execute"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "report_flag",
        "description": "Report a discovered flag",
        "parameters": {
            "type": "object",
            "properties": {
                "flag": {"type": "string", "description": "The flag value found"},
                "location": {"type": "string", "description": "Where the flag was found"},
                "method": {"type": "string", "description": "How the flag was obtained"}
            },
            "required": ["flag"]
        }
    }
]


class AutonomousAgent:
    """
    Fully autonomous penetration testing agent using LangGraph.
    
    Workflow:
    1. User provides target and objective
    2. Agent plans attack strategy
    3. Agent executes tools based on plan
    4. Agent analyzes results
    5. Agent adjusts plan if needed
    6. Repeat until objective complete or max iterations
    
    Example:
        agent = AutonomousAgent()
        result = await agent.run("10.10.138.70", "Find all flags")
    """
    
    SYSTEM_PROMPT = """You are RedClaw, an elite autonomous penetration testing AI.

Your mission: Systematically attack the target and achieve the objective.

## Your Capabilities
You have access to security tools. Use them strategically:
- nmap_scan: Port and service discovery
- gobuster_scan: Web directory enumeration
- nikto_scan: Web vulnerability scanning
- curl_request: HTTP requests
- ssh_connect: SSH access
- ftp_connect: FTP access
- read_file: Read files
- bash_command: Custom commands
- report_flag: Record found flags

## Attack Methodology
1. **Recon**: Start with nmap to find open ports
2. **Enumerate**: Explore each service (web, ftp, ssh, etc.)
3. **Exploit**: Try default creds, known vulns, misconfigs
4. **Post-Exploit**: Read sensitive files, find flags
5. **Report**: Document all findings

## Important Rules
- Be systematic and thorough
- Check common paths: /robots.txt, /.git, /admin, /backup
- Try anonymous FTP if port 21 is open
- Try common credentials (admin:admin, root:root, etc.)
- Look for flags in files, comments, headers
- ALWAYS call report_flag when you find a flag

## Response Format
Analyze the situation, then call tools. After each tool result, analyze and decide next steps.
Think step-by-step but act decisively.
"""

    def __init__(
        self,
        llm: Optional[RedClawLLM] = None,
        tool_executor: Optional[ToolExecutor] = None,
        memory: Optional[MemoryManager] = None,
        callbacks: Optional[List[Callable]] = None,
        verbose: bool = True,
        workspace: Optional[str] = None
    ):
        self.llm = llm or get_llm_client()
        self.tool_executor = tool_executor or ToolExecutor()
        self.memory = memory
        self.callbacks = callbacks or []
        self.verbose = verbose
        self.workspace = workspace
        
        # Event handlers for CLI integration
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Build the agent graph
        self.graph = self._build_graph() if LANGGRAPH_AVAILABLE else None
        
    def _build_graph(self) -> 'StateGraph':
        """Build the LangGraph agent workflow"""
        if not LANGGRAPH_AVAILABLE:
            return None
            
        # Define the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("analyze", self._analyze_node)
        
        # Set entry point
        workflow.set_entry_point("plan")
        
        # Add edges
        workflow.add_conditional_edges(
            "plan",
            self._should_continue,
            {
                "continue": "execute",
                "end": END
            }
        )
        workflow.add_edge("execute", "analyze")
        workflow.add_conditional_edges(
            "analyze",
            self._should_continue,
            {
                "continue": "plan",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def _should_continue(self, state: AgentState) -> Literal["continue", "end"]:
        """Decide whether to continue the agent loop"""
        # Check termination conditions
        if state.iteration >= state.max_iterations:
            return "end"
        if state.error:
            return "end"
        if state.phase == AgentPhase.COMPLETED:
            return "end"
        if len(state.flags) >= 3:  # Found target flags
            return "end"
        return "continue"
    
    async def _plan_node(self, state: AgentState) -> AgentState:
        """Planning node - decide what to do next"""
        self._emit("plan_start", {"iteration": state.iteration})
        
        # Build context message
        context = self._build_context(state)
        
        # Ask LLM for next action
        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
            Message(role="user", content=context)
        ]
        
        response = await self.llm.chat(
            messages,
            tools=TOOL_DEFINITIONS,
            temperature=0.3
        )
        
        # Parse the response for tool calls
        if response.tool_calls:
            state.current_plan = [
                f"{tc['name']}({json.dumps(tc['arguments'])})"
                for tc in response.tool_calls
            ]
        
        state.messages.append({
            "role": "assistant",
            "content": response.content,
            "tool_calls": response.tool_calls
        })
        
        self._emit("plan_complete", {"plan": state.current_plan})
        return state
    
    async def _execute_node(self, state: AgentState) -> AgentState:
        """Execution node - run the planned tools"""
        self._emit("execute_start", {"plan": state.current_plan})
        
        results = []
        for i, tool_call in enumerate(state.messages[-1].get("tool_calls", [])):
            tool_name = tool_call["name"]
            tool_args = tool_call["arguments"]
            
            self._emit("tool_start", {"tool": tool_name, "args": tool_args})
            
            # Execute the tool
            result = await self._execute_tool(tool_name, tool_args, state)
            
            results.append({
                "tool": tool_name,
                "args": tool_args,
                "result": result
            })
            
            state.tool_history.append({
                "tool": tool_name,
                "args": tool_args,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
            self._emit("tool_complete", {"tool": tool_name, "result": result})
        
        # Add results to messages
        state.messages.append({
            "role": "tool",
            "results": results
        })
        
        state.iteration += 1
        return state
    
    async def _analyze_node(self, state: AgentState) -> AgentState:
        """Analysis node - interpret results and update state"""
        self._emit("analyze_start", {"iteration": state.iteration})
        
        # Get the latest tool results
        results = state.messages[-1].get("results", [])
        
        for r in results:
            # Parse nmap results
            if r["tool"] == "nmap_scan":
                self._parse_nmap_result(r["result"], state)
            
            # Check for flags in any output
            self._check_for_flags(r["result"], state)
            
            # Update phase based on progress
            self._update_phase(state)
        
        self._emit("analyze_complete", {
            "ports": len(state.discovered_ports),
            "services": len(state.discovered_services),
            "flags": len(state.flags),
            "phase": state.phase.value
        })
        
        return state
    
    async def _execute_tool(
        self, 
        tool_name: str, 
        args: Dict[str, Any],
        state: AgentState
    ) -> str:
        """Execute a single tool and return result"""
        
        # Map tool names to commands
        if tool_name == "nmap_scan":
            target = args.get("target", state.target)
            ports = args.get("ports", "1-65535")
            scan_type = args.get("scan_type", "default")
            cmd = self.tool_executor.get_nmap_command(target, ports, scan_type)
            
        elif tool_name == "gobuster_scan":
            url = args.get("url")
            wordlist = args.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
            extensions = args.get("extensions", "php,html,txt")
            cmd = f"gobuster dir -u {url} -w {wordlist} -x {extensions} -q"
            
        elif tool_name == "curl_request":
            url = args.get("url")
            method = args.get("method", "GET")
            data = args.get("data", "")
            cmd = f"curl -s -X {method} {url}"
            if data:
                cmd += f" -d '{data}'"
                
        elif tool_name == "nikto_scan":
            target = args.get("target")
            port = args.get("port", 80)
            cmd = f"nikto -h {target} -p {port} -Tuning x 6"
            
        elif tool_name == "ssh_connect":
            host = args.get("host")
            user = args.get("username")
            password = args.get("password", "")
            command = args.get("command", "id; cat /etc/passwd; find / -name 'flag*' 2>/dev/null")
            if password:
                cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no {user}@{host} '{command}'"
            else:
                cmd = f"ssh -o StrictHostKeyChecking=no {user}@{host} '{command}'"
                
        elif tool_name == "ftp_connect":
            host = args.get("host")
            user = args.get("username", "anonymous")
            password = args.get("password", "anonymous@")
            cmd = f"curl -s ftp://{user}:{password}@{host}/"
            
        elif tool_name == "read_file":
            path = args.get("path")
            method = args.get("method", "curl")
            if "http" in path:
                cmd = f"curl -s {path}"
            else:
                cmd = f"cat {path}"
                
        elif tool_name == "bash_command":
            cmd = args.get("command")
            
        elif tool_name == "report_flag":
            flag = args.get("flag")
            location = args.get("location", "unknown")
            method = args.get("method", "unknown")
            state.flags.append({
                "flag": flag,
                "location": location,
                "method": method,
                "timestamp": datetime.now().isoformat()
            })
            return f"Flag recorded: {flag}"
            
        else:
            return f"Unknown tool: {tool_name}"
        
        # Execute the command
        result = await self.tool_executor.execute(cmd)
        
        if result.return_code != 0 and result.stderr:
            return f"Error: {result.stderr}"
        
        return result.stdout or result.stderr or "No output"
    
    def _parse_nmap_result(self, output: str, state: AgentState):
        """Parse nmap output and update state"""
        parsed = self.tool_executor.parse_nmap_output(output)
        
        for port in parsed.get("open_ports", []):
            if port not in [p["port"] for p in state.discovered_ports]:
                state.discovered_ports.append({"port": port})
                
        for service in parsed.get("services", []):
            state.discovered_services.append(service)
    
    def _check_for_flags(self, output: str, state: AgentState):
        """Check output for flag patterns"""
        # Common flag patterns
        patterns = [
            r'flag\{[^}]+\}',
            r'FLAG\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'CTF\{[^}]+\}',
            r'THM\{[^}]+\}',
            r'HTB\{[^}]+\}',
            r'[a-f0-9]{32}',  # MD5 hash (common flag format)
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                if match not in [f["flag"] for f in state.flags]:
                    state.flags.append({
                        "flag": match,
                        "location": "auto-detected",
                        "method": "pattern-match"
                    })
                    self._emit("flag_found", {"flag": match})
    
    def _update_phase(self, state: AgentState):
        """Update agent phase based on progress"""
        if not state.discovered_ports:
            state.phase = AgentPhase.RECONNAISSANCE
        elif not state.discovered_services:
            state.phase = AgentPhase.SCANNING
        elif not state.discovered_vulns:
            state.phase = AgentPhase.ENUMERATION
        elif not state.flags:
            state.phase = AgentPhase.EXPLOITATION
        elif len(state.flags) >= 1:
            state.phase = AgentPhase.POST_EXPLOITATION
        
        if len(state.flags) >= 3:
            state.phase = AgentPhase.COMPLETED
    
    def _build_context(self, state: AgentState) -> str:
        """Build context message for LLM"""
        context = f"""## Current Mission
Target: {state.target}
Objective: {state.objective}
Phase: {state.phase.value}
Iteration: {state.iteration}/{state.max_iterations}

## Discovered Information
Open Ports: {len(state.discovered_ports)}
{json.dumps(state.discovered_ports[:10], indent=2) if state.discovered_ports else "None yet"}

Services: {len(state.discovered_services)}
{json.dumps(state.discovered_services[:10], indent=2) if state.discovered_services else "None yet"}

Flags Found: {len(state.flags)}
{json.dumps([f["flag"] for f in state.flags], indent=2) if state.flags else "None yet"}

## Recent Tool Results
"""
        # Add last 3 tool results
        for msg in state.messages[-6:]:
            if msg.get("role") == "tool":
                for r in msg.get("results", [])[:2]:
                    output = r.get("result", "")[:500]
                    context += f"\n### {r['tool']}\n```\n{output}\n```\n"
        
        context += "\n## Your Task\nAnalyze the current state and call the next appropriate tool(s) to progress toward the objective."
        
        return context
    
    def _emit(self, event: str, data: Any = None):
        """Emit event to callbacks and registered handlers"""
        if self.verbose:
            print(f"[Agent] {event}: {data}")
        
        # Call legacy callbacks
        for cb in self.callbacks:
            try:
                cb(event, data)
            except Exception:
                pass
        
        # Call event-specific handlers
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    handler(data)
                except Exception:
                    pass
    
    def on(self, event: str, handler: Callable):
        """
        Register an event handler
        
        Events:
            - agent_start: Agent started
            - agent_complete: Agent finished
            - plan_start/complete: Planning phase
            - execute_start: Execution started
            - tool_start: Tool starting {tool, args}
            - tool_complete: Tool finished {tool, result}
            - analyze_start/complete: Analysis phase
            - phase_change: Agent phase changed
            - flag_found: Flag discovered {flag}
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    async def run(
        self,
        target: str,
        objective: str = "Find all flags and report vulnerabilities",
        max_iterations: int = 50
    ) -> Dict[str, Any]:
        """
        Run the autonomous agent
        
        Args:
            target: Target IP or hostname
            objective: What to achieve
            max_iterations: Maximum tool calls
            
        Returns:
            Dict with findings, flags, and report
        """
        initial_state = AgentState(
            target=target,
            objective=objective,
            max_iterations=max_iterations
        )
        
        self._emit("agent_start", {"target": target, "objective": objective})
        
        if self.graph:
            # Use LangGraph
            final_state = await self.graph.ainvoke(initial_state)
        else:
            # Fallback: Simple loop
            final_state = await self._simple_loop(initial_state)
        
        self._emit("agent_complete", {
            "flags": len(final_state.flags),
            "iterations": final_state.iteration
        })
        
        return {
            "success": len(final_state.flags) > 0,
            "flags": final_state.flags,
            "ports": final_state.discovered_ports,
            "services": final_state.discovered_services,
            "vulnerabilities": final_state.discovered_vulns,
            "iterations": final_state.iteration,
            "tool_history": final_state.tool_history
        }
    
    async def _simple_loop(self, state: AgentState) -> AgentState:
        """Simple agent loop without LangGraph"""
        while self._should_continue(state) == "continue":
            state = await self._plan_node(state)
            if self._should_continue(state) == "end":
                break
            state = await self._execute_node(state)
            state = await self._analyze_node(state)
        return state


# Convenience function
async def auto_pwn(target: str, objective: str = "Find all flags") -> Dict:
    """
    One-line autonomous penetration test
    
    Usage:
        result = await auto_pwn("10.10.138.70")
        print(result["flags"])
    """
    agent = AutonomousAgent(verbose=True)
    return await agent.run(target, objective)
