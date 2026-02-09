"""
RedClaw - Tool Executor
Safely executes security tools in a sandboxed environment
"""

import asyncio
import subprocess
import shlex
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import os
import re


class ToolCategory(Enum):
    """Categories of security tools"""
    RECON = "reconnaissance"
    SCANNING = "scanning"
    ENUMERATION = "enumeration"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    WIRELESS = "wireless"
    PASSWORD = "password"
    WEB = "web"


@dataclass
class ToolResult:
    """Result from tool execution"""
    command: str
    stdout: str
    stderr: str
    return_code: int
    timed_out: bool = False


class ToolExecutor:
    """
    Executes security tools with safety controls and output parsing.
    Designed to run on Kali Linux with standard security tools installed.
    """
    
    # Allowed tools whitelist
    ALLOWED_TOOLS = {
        # Reconnaissance
        "whois", "dig", "nslookup", "host", "dnsrecon", "dnsenum",
        "sublist3r", "amass", "theHarvester",
        
        # Scanning
        "nmap", "masscan", "rustscan",
        
        # Enumeration
        "enum4linux", "smbclient", "rpcclient", "ldapsearch",
        "snmpwalk", "nikto", "dirb", "gobuster", "feroxbuster",
        
        # Web
        "sqlmap", "wpscan", "nuclei", "httpx", "whatweb",
        
        # Password
        "hydra", "john", "hashcat", "medusa",
        
        # Exploitation
        "msfconsole", "searchsploit",
        
        # Utility
        "curl", "wget", "nc", "netcat", "socat", "python3", "bash"
    }
    
    # Dangerous patterns to block
    BLOCKED_PATTERNS = [
        r"rm\s+-rf",
        r"mkfs\.",
        r"dd\s+if=",
        r":\(\)\s*{\s*:.*}",  # Fork bomb
        r">\s*/dev/sd",
        r"chmod\s+777\s+/",
    ]
    
    def __init__(
        self,
        timeout: int = 300,
        sandbox: bool = False,
        allowed_hosts: Optional[List[str]] = None
    ):
        self.timeout = timeout
        self.sandbox = sandbox
        self.allowed_hosts = allowed_hosts or []
        self.history: List[ToolResult] = []
    
    def _validate_command(self, command: str) -> bool:
        """Validate command against security rules"""
        # Check for blocked patterns
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False
        
        # Extract base tool
        parts = shlex.split(command)
        if not parts:
            return False
        
        base_tool = os.path.basename(parts[0])
        
        # Check whitelist
        if base_tool not in self.ALLOWED_TOOLS:
            return False
        
        return True
    
    def _check_scope(self, command: str) -> bool:
        """Check if command targets are within scope"""
        if not self.allowed_hosts:
            return True  # No scope restriction
        
        # Extract potential targets from command
        # This is a simplified check
        for host in self.allowed_hosts:
            if host in command:
                return True
        
        return False
    
    async def execute(self, command: str) -> ToolResult:
        """
        Execute a tool command
        
        Args:
            command: The command to execute
            
        Returns:
            ToolResult with output and status
        """
        # Validate
        if not self._validate_command(command):
            return ToolResult(
                command=command,
                stdout="",
                stderr="Command not allowed by security policy",
                return_code=-1
            )
        
        # Scope check
        if not self._check_scope(command):
            return ToolResult(
                command=command,
                stdout="",
                stderr="Target not in scope",
                return_code=-1
            )
        
        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/tmp"
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
                
                result = ToolResult(
                    command=command,
                    stdout=stdout.decode('utf-8', errors='replace'),
                    stderr=stderr.decode('utf-8', errors='replace'),
                    return_code=process.returncode or 0
                )
            
            except asyncio.TimeoutError:
                process.kill()
                result = ToolResult(
                    command=command,
                    stdout="",
                    stderr=f"Command timed out after {self.timeout} seconds",
                    return_code=-1,
                    timed_out=True
                )
        
        except Exception as e:
            result = ToolResult(
                command=command,
                stdout="",
                stderr=str(e),
                return_code=-1
            )
        
        self.history.append(result)
        return result
    
    def execute_sync(self, command: str) -> ToolResult:
        """Synchronous execution wrapper"""
        return asyncio.run(self.execute(command))
    
    def get_nmap_command(
        self,
        target: str,
        ports: str = "1-1000",
        scan_type: str = "default",
        extra_args: str = ""
    ) -> str:
        """Generate nmap command based on scan type"""
        base = f"nmap {target}"
        
        scan_configs = {
            "default": f"-sV -sC -p {ports}",
            "quick": f"-T4 -F",
            "full": f"-sV -sC -p- -T4",
            "stealth": f"-sS -T2 -p {ports}",
            "vuln": f"-sV --script=vuln -p {ports}",
            "udp": f"-sU -T4 --top-ports 100"
        }
        
        args = scan_configs.get(scan_type, scan_configs["default"])
        return f"{base} {args} {extra_args}".strip()
    
    def parse_nmap_output(self, output: str) -> Dict:
        """Parse nmap output to structured format"""
        result = {
            "hosts": [],
            "open_ports": [],
            "services": []
        }
        
        for line in output.split('\n'):
            # Parse open ports
            if '/tcp' in line or '/udp' in line:
                parts = line.split()
                if len(parts) >= 3 and 'open' in line:
                    port_proto = parts[0]
                    state = parts[1]
                    service = parts[2] if len(parts) > 2 else "unknown"
                    
                    result["open_ports"].append(port_proto)
                    result["services"].append({
                        "port": port_proto,
                        "state": state,
                        "service": service
                    })
        
        return result
