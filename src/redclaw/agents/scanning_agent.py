"""
RedClaw - Scanning Agent
Port scanning, service detection, vulnerability identification
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import re

from ..core.llm_client import RedClawLLM, Message
from ..tools.executor import ToolExecutor


@dataclass
class ScanResult:
    """Scan finding"""
    tool: str
    scan_type: str
    target: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Service:
    """Discovered service"""
    port: int
    protocol: str
    state: str
    service: str
    version: str = ""
    banner: str = ""


class ScanningAgent:
    """
    Scanning Agent - Port and service discovery
    
    Capabilities:
    - Port scanning (nmap, masscan)
    - Service detection
    - OS fingerprinting
    - Banner grabbing
    - Vulnerability scanning
    """
    
    def __init__(self, llm: RedClawLLM, executor: ToolExecutor):
        self.llm = llm
        self.executor = executor
        self.results: List[ScanResult] = []
        self.services: List[Service] = []
    
    async def run_port_scan(
        self,
        target: str,
        ports: str = "1-1000",
        scan_type: str = "default"
    ) -> ScanResult:
        """Run nmap port scan"""
        nmap_cmd = self.executor.get_nmap_command(
            target=target,
            ports=ports,
            scan_type=scan_type
        )
        
        result = await self.executor.execute(nmap_cmd)
        parsed = self.executor.parse_nmap_output(result.stdout)
        
        # Extract services
        for svc in parsed.get("services", []):
            port_num = int(svc["port"].split('/')[0])
            proto = svc["port"].split('/')[1] if '/' in svc["port"] else "tcp"
            
            service = Service(
                port=port_num,
                protocol=proto,
                state=svc.get("state", "unknown"),
                service=svc.get("service", "unknown")
            )
            self.services.append(service)
        
        scan_result = ScanResult(
            tool="nmap",
            scan_type=scan_type,
            target=target,
            data={
                "raw": result.stdout,
                "parsed": parsed,
                "open_ports": parsed.get("open_ports", [])
            }
        )
        self.results.append(scan_result)
        return scan_result
    
    async def run_service_detection(self, target: str) -> ScanResult:
        """Detailed service version detection"""
        # Get open ports from previous scans
        open_ports = []
        for svc in self.services:
            if svc.state == "open":
                open_ports.append(str(svc.port))
        
        if not open_ports:
            open_ports = ["22", "80", "443", "8080"]
        
        port_str = ",".join(open_ports[:50])  # Limit to 50 ports
        
        result = await self.executor.execute(
            f"nmap -sV -sC -p {port_str} {target}"
        )
        
        scan_result = ScanResult(
            tool="nmap",
            scan_type="service_detection",
            target=target,
            data={"raw": result.stdout}
        )
        self.results.append(scan_result)
        return scan_result
    
    async def run_vuln_scan(self, target: str) -> ScanResult:
        """Run vulnerability scan"""
        # Get open ports
        open_ports = [str(svc.port) for svc in self.services if svc.state == "open"]
        port_str = ",".join(open_ports[:20]) if open_ports else "22,80,443"
        
        result = await self.executor.execute(
            f"nmap --script=vuln -p {port_str} {target}"
        )
        
        scan_result = ScanResult(
            tool="nmap",
            scan_type="vuln_scan",
            target=target,
            data={"raw": result.stdout}
        )
        self.results.append(scan_result)
        return scan_result
    
    async def run_nuclei_scan(self, target: str) -> ScanResult:
        """Run nuclei vulnerability scanner"""
        result = await self.executor.execute(
            f"nuclei -u {target} -severity medium,high,critical -silent"
        )
        
        scan_result = ScanResult(
            tool="nuclei",
            scan_type="vuln_templates",
            target=target,
            data={
                "raw": result.stdout,
                "findings": result.stdout.strip().split('\n') if result.stdout else []
            }
        )
        self.results.append(scan_result)
        return scan_result
    
    async def analyze_with_llm(self) -> str:
        """LLM analysis of scan results"""
        services_info = "\n".join([
            f"Port {s.port}/{s.protocol}: {s.service} {s.version}"
            for s in self.services
        ])
        
        vuln_info = ""
        for r in self.results:
            if r.scan_type in ["vuln_scan", "vuln_templates"]:
                vuln_info += f"\n{r.tool}: {r.data.get('raw', '')[:1000]}"
        
        messages = [
            Message(role="system", content="""You are a penetration testing expert.
Analyze the scanning results and identify:
1. High-value targets for exploitation
2. Potential vulnerabilities
3. Recommended exploits or attack vectors
4. Priority order for exploitation"""),
            Message(role="user", content=f"""
Services discovered:
{services_info}

Vulnerability scan results:
{vuln_info[:2000]}
""")
        ]
        
        response = self.llm.chat(messages, max_tokens=1500)
        return response.content
    
    async def run_full_scan(
        self,
        target: str,
        ports: str = "1-1000",
        include_vuln: bool = True
    ) -> Dict[str, Any]:
        """Run complete scanning phase"""
        # Port scan
        await self.run_port_scan(target, ports)
        
        # Service detection
        await self.run_service_detection(target)
        
        # Vulnerability scanning
        if include_vuln:
            await self.run_vuln_scan(target)
            
            # Check if target is a web service
            web_ports = [s for s in self.services if s.port in [80, 443, 8080, 8443]]
            if web_ports:
                url = f"http://{target}" if 80 in [s.port for s in web_ports] else f"https://{target}"
                await self.run_nuclei_scan(url)
        
        analysis = await self.analyze_with_llm()
        
        return {
            "target": target,
            "services": [
                {"port": s.port, "protocol": s.protocol, "service": s.service, "state": s.state}
                for s in self.services
            ],
            "scan_results": len(self.results),
            "analysis": analysis
        }
