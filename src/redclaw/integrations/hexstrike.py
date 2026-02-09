"""
RedClaw - HexStrike-AI MCP Integration
Connection to HexStrike-AI tool server
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio
import json
import os
import httpx


@dataclass
class ToolDefinition:
    """Tool definition from HexStrike-AI"""
    name: str
    description: str
    parameters: Dict[str, Any]
    category: str
    requires_confirmation: bool = False


@dataclass
class ToolCallResult:
    """Result of a tool call"""
    tool_name: str
    success: bool
    output: str
    error: Optional[str] = None
    execution_time_ms: int = 0


class HexStrikeClient:
    """
    HexStrike-AI MCP Client
    
    Connects to the HexStrike-AI MCP server (default port 8888)
    to execute security tools in an isolated environment.
    
    Features:
    - Tool discovery
    - Isolated execution
    - Result parsing
    - Session management
    """
    
    def __init__(
        self,
        endpoint: str = None,
        timeout: int = 300
    ):
        self.endpoint = endpoint or os.getenv(
            "HEXSTRIKE_ENDPOINT",
            "http://localhost:8888"
        )
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.available_tools: Dict[str, ToolDefinition] = {}
        self.session_id: Optional[str] = None
    
    async def connect(self) -> bool:
        """Connect to HexStrike-AI server"""
        try:
            response = await self.client.get(f"{self.endpoint}/health")
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
                return True
        except Exception as e:
            print(f"HexStrike connection failed: {e}")
        return False
    
    async def discover_tools(self) -> List[ToolDefinition]:
        """Discover available tools"""
        try:
            response = await self.client.get(f"{self.endpoint}/tools")
            if response.status_code == 200:
                data = response.json()
                
                for tool_data in data.get("tools", []):
                    tool = ToolDefinition(
                        name=tool_data["name"],
                        description=tool_data.get("description", ""),
                        parameters=tool_data.get("parameters", {}),
                        category=tool_data.get("category", "general"),
                        requires_confirmation=tool_data.get("dangerous", False)
                    )
                    self.available_tools[tool.name] = tool
                
                return list(self.available_tools.values())
        except Exception as e:
            print(f"Tool discovery failed: {e}")
        
        return []
    
    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> ToolCallResult:
        """Call a tool"""
        try:
            response = await self.client.post(
                f"{self.endpoint}/tools/{tool_name}",
                json={
                    "session_id": self.session_id,
                    "parameters": parameters
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return ToolCallResult(
                    tool_name=tool_name,
                    success=data.get("success", True),
                    output=data.get("output", ""),
                    execution_time_ms=data.get("execution_time_ms", 0)
                )
            else:
                return ToolCallResult(
                    tool_name=tool_name,
                    success=False,
                    output="",
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            return ToolCallResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=str(e)
            )
    
    async def run_nmap(
        self,
        target: str,
        ports: str = "1-1000",
        options: str = "-sV"
    ) -> ToolCallResult:
        """Run nmap scan"""
        return await self.call_tool("nmap", {
            "target": target,
            "ports": ports,
            "options": options
        })
    
    async def run_nikto(
        self,
        target: str,
        options: str = ""
    ) -> ToolCallResult:
        """Run nikto web scanner"""
        return await self.call_tool("nikto", {
            "target": target,
            "options": options
        })
    
    async def run_sqlmap(
        self,
        url: str,
        data: str = "",
        options: str = "--batch"
    ) -> ToolCallResult:
        """Run sqlmap"""
        return await self.call_tool("sqlmap", {
            "url": url,
            "data": data,
            "options": options
        })
    
    async def run_searchsploit(
        self,
        query: str
    ) -> ToolCallResult:
        """Search ExploitDB"""
        return await self.call_tool("searchsploit", {
            "query": query
        })
    
    async def run_metasploit(
        self,
        module: str,
        options: Dict[str, str]
    ) -> ToolCallResult:
        """Run Metasploit module"""
        return await self.call_tool("metasploit", {
            "module": module,
            "options": options
        })
    
    async def run_nuclei(
        self,
        target: str,
        templates: str = "",
        severity: str = "medium,high,critical"
    ) -> ToolCallResult:
        """Run nuclei vulnerability scanner"""
        return await self.call_tool("nuclei", {
            "target": target,
            "templates": templates,
            "severity": severity
        })
    
    async def run_hydra(
        self,
        target: str,
        service: str,
        userlist: str,
        passlist: str,
        options: str = ""
    ) -> ToolCallResult:
        """Run hydra brute forcer"""
        return await self.call_tool("hydra", {
            "target": target,
            "service": service,
            "userlist": userlist,
            "passlist": passlist,
            "options": options
        })
    
    async def run_gobuster(
        self,
        url: str,
        wordlist: str = "/usr/share/wordlists/dirb/common.txt",
        mode: str = "dir"
    ) -> ToolCallResult:
        """Run gobuster directory brute force"""
        return await self.call_tool("gobuster", {
            "url": url,
            "wordlist": wordlist,
            "mode": mode
        })
    
    async def get_results(self, task_id: str) -> Dict:
        """Get results for async task"""
        try:
            response = await self.client.get(
                f"{self.endpoint}/results/{task_id}"
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Get results failed: {e}")
        return {}
    
    async def close(self):
        """Close connection"""
        await self.client.aclose()


class MockHexStrikeClient(HexStrikeClient):
    """
    Mock HexStrike client for testing without server
    Falls back to local tool execution
    """
    
    def __init__(self, executor=None):
        super().__init__()
        self.executor = executor
        self._init_mock_tools()
    
    def _init_mock_tools(self):
        """Initialize mock tool definitions"""
        mock_tools = [
            ("nmap", "Network scanner", "scanning"),
            ("nikto", "Web server scanner", "web"),
            ("sqlmap", "SQL injection tool", "web"),
            ("searchsploit", "Exploit database search", "exploitation"),
            ("nuclei", "Vulnerability scanner", "scanning"),
            ("gobuster", "Directory brute forcer", "web"),
            ("hydra", "Network login cracker", "passwords"),
            ("metasploit", "Exploitation framework", "exploitation"),
        ]
        
        for name, desc, cat in mock_tools:
            self.available_tools[name] = ToolDefinition(
                name=name,
                description=desc,
                parameters={},
                category=cat
            )
    
    async def connect(self) -> bool:
        """Mock connect always succeeds"""
        self.session_id = "mock_session"
        return True
    
    async def discover_tools(self) -> List[ToolDefinition]:
        """Return mock tools"""
        return list(self.available_tools.values())
    
    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> ToolCallResult:
        """Execute tool locally if executor available"""
        if self.executor:
            # Build command from tool name and parameters
            if tool_name == "nmap":
                cmd = f"nmap {parameters.get('options', '')} -p {parameters.get('ports', '1-1000')} {parameters['target']}"
            elif tool_name == "searchsploit":
                cmd = f"searchsploit {parameters['query']}"
            else:
                cmd = f"{tool_name} {' '.join(str(v) for v in parameters.values())}"
            
            result = await self.executor.execute(cmd)
            
            return ToolCallResult(
                tool_name=tool_name,
                success=result.return_code == 0,
                output=result.stdout,
                error=result.stderr if result.return_code != 0 else None
            )
        
        return ToolCallResult(
            tool_name=tool_name,
            success=False,
            output="",
            error="No executor available"
        )


def get_hexstrike_client(
    use_mock: bool = False,
    executor=None
) -> HexStrikeClient:
    """Get HexStrike client instance"""
    if use_mock:
        return MockHexStrikeClient(executor)
    
    return HexStrikeClient()
