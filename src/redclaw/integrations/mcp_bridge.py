"""
RedClaw MCP Bridge - Integration with Model Context Protocol servers
Provides unified access to GitHub, Firecrawl, and Kaggle MCP tools
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum


class MCPServerType(Enum):
    """Supported MCP server types"""
    GITHUB = "github"
    FIRECRAWL = "firecrawl"
    KAGGLE = "kaggle"


@dataclass
class MCPToolCall:
    """Represents an MCP tool call"""
    server: MCPServerType
    tool_name: str
    arguments: Dict[str, Any]


@dataclass
class MCPToolResult:
    """Result from MCP tool execution"""
    success: bool
    data: Any
    error: Optional[str] = None


class MCPBridge:
    """
    Bridge to MCP servers for enhanced capabilities.
    
    Provides access to:
    - GitHub MCP: Code search, repo analysis, PR review
    - Firecrawl MCP: Web scraping, search
    - Kaggle MCP: Dataset access, notebook execution
    """
    
    # Tool definitions for LLM
    GITHUB_TOOLS = [
        {
            "name": "github_search_code",
            "description": "Search for code across GitHub repositories",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query with GitHub code search syntax"},
                    "per_page": {"type": "integer", "description": "Results per page (max 100)"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "github_get_file",
            "description": "Get contents of a file from a GitHub repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["owner", "repo", "path"]
            }
        },
        {
            "name": "github_search_issues",
            "description": "Search GitHub issues and PRs",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Issue search query"}
                },
                "required": ["query"]
            }
        }
    ]
    
    FIRECRAWL_TOOLS = [
        {
            "name": "firecrawl_scrape",
            "description": "Scrape content from a web page",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to scrape"},
                    "formats": {"type": "array", "items": {"type": "string"}, "description": "Output formats (markdown, html)"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "firecrawl_search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Number of results"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "firecrawl_map",
            "description": "Discover all URLs on a website",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Base URL to map"}
                },
                "required": ["url"]
            }
        }
    ]
    
    KAGGLE_TOOLS = [
        {
            "name": "kaggle_search_datasets",
            "description": "Search Kaggle datasets",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "Search query"}
                },
                "required": ["search"]
            }
        },
        {
            "name": "kaggle_search_notebooks",
            "description": "Search Kaggle notebooks",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "Search query"}
                },
                "required": ["search"]
            }
        }
    ]
    
    def __init__(
        self,
        github_enabled: bool = True,
        firecrawl_enabled: bool = True,
        kaggle_enabled: bool = True
    ):
        self.github_enabled = github_enabled
        self.firecrawl_enabled = firecrawl_enabled
        self.kaggle_enabled = kaggle_enabled
        
        # Track available tools
        self._tools_registry: Dict[str, Dict] = {}
        self._init_tools_registry()
    
    def _init_tools_registry(self):
        """Initialize the tools registry"""
        if self.github_enabled:
            for tool in self.GITHUB_TOOLS:
                self._tools_registry[tool["name"]] = {
                    "server": MCPServerType.GITHUB,
                    "definition": tool
                }
        
        if self.firecrawl_enabled:
            for tool in self.FIRECRAWL_TOOLS:
                self._tools_registry[tool["name"]] = {
                    "server": MCPServerType.FIRECRAWL,
                    "definition": tool
                }
        
        if self.kaggle_enabled:
            for tool in self.KAGGLE_TOOLS:
                self._tools_registry[tool["name"]] = {
                    "server": MCPServerType.KAGGLE,
                    "definition": tool
                }
    
    def get_all_tools(self) -> List[Dict]:
        """Get all available tool definitions for LLM"""
        return [info["definition"] for info in self._tools_registry.values()]
    
    def get_tool(self, name: str) -> Optional[Dict]:
        """Get a specific tool definition"""
        if name in self._tools_registry:
            return self._tools_registry[name]["definition"]
        return None
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """
        Execute an MCP tool
        
        Note: This is a bridge interface. Actual MCP execution happens via
        the MCP protocol. This method prepares the call for the MCP server.
        """
        if tool_name not in self._tools_registry:
            return MCPToolResult(
                success=False,
                data=None,
                error=f"Unknown tool: {tool_name}"
            )
        
        tool_info = self._tools_registry[tool_name]
        server = tool_info["server"]
        
        # Format the MCP call
        mcp_call = {
            "server": server.value,
            "tool": tool_name,
            "arguments": arguments
        }
        
        # In a real implementation, this would:
        # 1. Connect to the MCP server
        # 2. Send the tool call
        # 3. Return the result
        
        # For now, return a placeholder
        return MCPToolResult(
            success=True,
            data=mcp_call,
            error=None
        )
    
    def format_for_cli(self, tool_name: str) -> str:
        """Format tool info for CLI display"""
        if tool_name not in self._tools_registry:
            return f"Unknown tool: {tool_name}"
        
        tool = self._tools_registry[tool_name]["definition"]
        server = self._tools_registry[tool_name]["server"]
        
        output = f"[{server.value}] {tool['name']}\n"
        output += f"  {tool['description']}\n"
        
        if "parameters" in tool:
            params = tool["parameters"].get("properties", {})
            required = tool["parameters"].get("required", [])
            
            for name, info in params.items():
                req_marker = "*" if name in required else ""
                output += f"  - {name}{req_marker}: {info.get('description', '')}\n"
        
        return output


class MCPToolRegistry:
    """
    Unified registry for all tools (local + MCP)
    """
    
    def __init__(self, mcp_bridge: Optional[MCPBridge] = None):
        self.mcp_bridge = mcp_bridge or MCPBridge()
        self._local_tools: Dict[str, Dict] = {}
    
    @property
    def local_tools(self) -> List[str]:
        """Get list of registered local tool names"""
        return list(self._local_tools.keys())
    
    def register_local_tool(self, name: str, definition: Dict, executor: Callable):
        """Register a local tool"""
        self._local_tools[name] = {
            "definition": definition,
            "executor": executor
        }
    
    def get_all_tool_definitions(self) -> List[Dict]:
        """Get all tool definitions (local + MCP)"""
        tools = []
        
        # Add local tools
        for info in self._local_tools.values():
            tools.append(info["definition"])
        
        # Add MCP tools
        tools.extend(self.mcp_bridge.get_all_tools())
        
        return tools
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool by name"""
        # Check local tools first
        if tool_name in self._local_tools:
            executor = self._local_tools[tool_name]["executor"]
            if asyncio.iscoroutinefunction(executor):
                return await executor(**arguments)
            return executor(**arguments)
        
        # Try MCP
        return await self.mcp_bridge.execute(tool_name, arguments)
    
    def list_tools(self) -> List[str]:
        """List all available tool names"""
        local = list(self._local_tools.keys())
        mcp = [t["name"] for t in self.mcp_bridge.get_all_tools()]
        return local + mcp
