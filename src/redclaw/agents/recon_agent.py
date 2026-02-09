"""
RedClaw - Reconnaissance Agent
Handles OSINT, DNS enumeration, subdomain discovery
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from ..core.llm_client import RedClawLLM, Message
from ..tools.executor import ToolExecutor


@dataclass
class ReconResult:
    """Reconnaissance finding"""
    source: str
    data_type: str  # dns, whois, subdomain, osint
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class ReconAgent:
    """
    Reconnaissance Agent - First phase of penetration testing
    
    Capabilities:
    - OSINT gathering
    - DNS enumeration
    - Subdomain discovery
    - Technology stack detection
    - Metadata extraction
    """
    
    def __init__(self, llm: RedClawLLM, executor: ToolExecutor):
        self.llm = llm
        self.executor = executor
        self.results: List[ReconResult] = []
    
    async def run_whois(self, target: str) -> ReconResult:
        """Run WHOIS lookup"""
        result = await self.executor.execute(f"whois {target}")
        
        recon = ReconResult(
            source="whois",
            data_type="whois",
            data={"raw": result.stdout, "target": target}
        )
        self.results.append(recon)
        return recon
    
    async def run_dns_enum(self, domain: str) -> ReconResult:
        """Run DNS enumeration"""
        commands = [
            f"dig {domain} ANY +noall +answer",
            f"dig {domain} MX +short",
            f"dig {domain} NS +short",
            f"dig {domain} TXT +short"
        ]
        
        outputs = {}
        for cmd in commands:
            result = await self.executor.execute(cmd)
            record_type = cmd.split()[2] if len(cmd.split()) > 2 else "ANY"
            outputs[record_type] = result.stdout
        
        recon = ReconResult(
            source="dig",
            data_type="dns",
            data=outputs
        )
        self.results.append(recon)
        return recon
    
    async def run_subdomain_enum(self, domain: str) -> ReconResult:
        """Enumerate subdomains"""
        # Try multiple tools
        result = await self.executor.execute(
            f"sublist3r -d {domain} -o /tmp/subdomains.txt 2>/dev/null || "
            f"amass enum -passive -d {domain} 2>/dev/null"
        )
        
        recon = ReconResult(
            source="subdomain_enum",
            data_type="subdomain",
            data={"subdomains": result.stdout.strip().split('\n') if result.stdout else []}
        )
        self.results.append(recon)
        return recon
    
    async def run_tech_detection(self, url: str) -> ReconResult:
        """Detect technology stack"""
        result = await self.executor.execute(f"whatweb -a 3 {url}")
        
        recon = ReconResult(
            source="whatweb",
            data_type="technology",
            data={"raw": result.stdout}
        )
        self.results.append(recon)
        return recon
    
    async def analyze_with_llm(self) -> str:
        """Use LLM to analyze reconnaissance results"""
        context = "\n".join([
            f"[{r.data_type}] {r.source}: {str(r.data)[:500]}"
            for r in self.results
        ])
        
        messages = [
            Message(role="system", content="""You are a penetration testing expert. 
Analyze the reconnaissance data and identify:
1. Potential attack vectors
2. Interesting findings
3. Recommended next steps for scanning phase"""),
            Message(role="user", content=f"Reconnaissance data:\n{context}")
        ]
        
        response = self.llm.chat(messages, max_tokens=1000)
        return response.content
    
    async def run_full_recon(self, target: str) -> Dict[str, Any]:
        """Run complete reconnaissance phase"""
        tasks = [
            self.run_whois(target),
            self.run_dns_enum(target),
        ]
        
        # Check if it looks like a domain
        if '.' in target and not target.replace('.', '').isdigit():
            tasks.append(self.run_subdomain_enum(target))
            tasks.append(self.run_tech_detection(f"https://{target}"))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        analysis = await self.analyze_with_llm()
        
        return {
            "target": target,
            "results": [
                {"type": r.data_type, "source": r.source, "data": r.data}
                for r in self.results
            ],
            "analysis": analysis
        }
