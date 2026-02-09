"""
RedClaw Agents - Reconnaissance Agent
Specialized agent for target reconnaissance and information gathering
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .base import BaseAgent, AgentCapability, AgentResult
from ..core.llm_client import RedClawLLM, Message


@dataclass
class ReconFinding:
    """Reconnaissance finding"""
    category: str  # dns, subdomain, tech, port, service
    data: Dict
    source: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


class ReconAgent(BaseAgent):
    """
    Reconnaissance Agent
    
    Specializes in:
    - DNS enumeration
    - Subdomain discovery
    - Technology detection
    - OSINT gathering
    - Port/service discovery
    """
    
    RECON_PROMPT = """You are a reconnaissance specialist conducting authorized security testing.

Target: {target}
Phase: Reconnaissance
Previous findings: {context}

Available tools:
{tools}

Analyze the target and plan reconnaissance steps:
1. DNS information gathering
2. Subdomain enumeration
3. Technology stack detection
4. Service identification
5. OSINT collection

Output a JSON plan:
{{
    "reasoning": "your analysis",
    "steps": [
        {{"tool": "tool_name", "args": {{"arg1": "value"}}, "purpose": "why"}}
    ],
    "priority": "high|medium|low"
}}"""

    def __init__(
        self,
        llm: RedClawLLM,
        **kwargs
    ):
        super().__init__(
            name="ReconAgent",
            description="Information gathering and reconnaissance specialist",
            llm=llm,
            capabilities=[
                AgentCapability.RECON,
                AgentCapability.OSINT
            ],
            **kwargs
        )
        
        self.findings: List[ReconFinding] = []
        
        # Register recon-specific tools
        self._register_recon_tools()
    
    def _register_recon_tools(self):
        """Register reconnaissance tools"""
        
        self.register_tool(
            "dns_lookup",
            self._dns_lookup,
            "Perform DNS lookup for domain"
        )
        
        self.register_tool(
            "subdomain_enum",
            self._subdomain_enum,
            "Enumerate subdomains for domain"
        )
        
        self.register_tool(
            "whois_lookup",
            self._whois_lookup,
            "Perform WHOIS lookup"
        )
        
        self.register_tool(
            "tech_detect",
            self._tech_detect,
            "Detect technologies used by target"
        )
        
        self.register_tool(
            "port_scan",
            self._port_scan,
            "Quick port scan"
        )
        
        self.register_tool(
            "osint_search",
            self._osint_search,
            "OSINT information search"
        )
    
    async def plan(self, objective: str, context: Dict = None) -> Dict:
        """Create reconnaissance plan"""
        
        tools_desc = "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.tools.items()
        ])
        
        prompt = self.RECON_PROMPT.format(
            target=objective,
            context=str(context or {}),
            tools=tools_desc
        )
        
        messages = [Message(role="user", content=prompt)]
        response = await self.llm.achat(messages, max_tokens=1024)
        
        return self._parse_plan(response.content)
    
    async def execute(
        self,
        target: str,
        depth: str = "normal"
    ) -> AgentResult:
        """Execute reconnaissance"""
        
        self.log(f"Starting reconnaissance on {target}")
        
        # Create plan
        plan = await self.plan(target)
        
        results = []
        errors = []
        
        # Execute steps
        for step in plan.get("steps", []):
            tool_name = step.get("tool")
            args = step.get("args", {})
            
            if tool_name not in self.tools:
                continue
            
            try:
                result = await self.execute_tool(tool_name, **args, target=target)
                results.append({
                    "tool": tool_name,
                    "purpose": step.get("purpose"),
                    "result": result
                })
                
                # Add to findings
                if result.get("success"):
                    self._add_finding(tool_name, result)
                    
            except Exception as e:
                errors.append({"tool": tool_name, "error": str(e)})
        
        # Analyze results
        analysis = await self._analyze_findings()
        
        return AgentResult(
            success=len(results) > 0,
            data={
                "target": target,
                "findings": [
                    {
                        "category": f.category,
                        "data": f.data,
                        "source": f.source
                    }
                    for f in self.findings
                ],
                "analysis": analysis,
                "plan": plan
            },
            message=f"Reconnaissance complete. {len(self.findings)} findings.",
            artifacts=results,
            errors=errors
        )
    
    def _add_finding(self, source: str, data: Dict):
        """Add finding to collection"""
        
        category_map = {
            "dns_lookup": "dns",
            "subdomain_enum": "subdomain",
            "whois_lookup": "whois",
            "tech_detect": "technology",
            "port_scan": "port",
            "osint_search": "osint"
        }
        
        self.findings.append(ReconFinding(
            category=category_map.get(source, "other"),
            data=data,
            source=source,
            confidence=0.8
        ))
    
    async def _analyze_findings(self) -> Dict:
        """Analyze collected findings"""
        
        if not self.findings:
            return {"summary": "No findings to analyze"}
        
        findings_text = "\n".join([
            f"- {f.category}: {str(f.data)[:200]}"
            for f in self.findings[:10]
        ])
        
        prompt = f"""Analyze these reconnaissance findings:

{findings_text}

Provide:
1. Key observations
2. Attack surface assessment
3. Recommended next steps
4. Priority targets

Output as JSON with keys: observations, attack_surface, next_steps, priority_targets"""

        messages = [Message(role="user", content=prompt)]
        response = await self.llm.achat(messages, max_tokens=1024)
        
        return self._parse_json(response.content) or {"raw": response.content}
    
    # ============ Tool Implementations ============
    
    async def _dns_lookup(self, target: str, **kwargs) -> Dict:
        """DNS lookup implementation"""
        import subprocess
        
        try:
            # A records
            result = subprocess.run(
                ["nslookup", target],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": True,
                "output": result.stdout,
                "records": self._parse_nslookup(result.stdout)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _subdomain_enum(self, target: str, **kwargs) -> Dict:
        """Subdomain enumeration"""
        import subprocess
        
        # Try subfinder if available
        try:
            result = subprocess.run(
                ["subfinder", "-d", target, "-silent"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            subdomains = [s.strip() for s in result.stdout.split("\n") if s.strip()]
            
            return {
                "success": True,
                "subdomains": subdomains,
                "count": len(subdomains)
            }
        except FileNotFoundError:
            # Fallback to basic DNS
            common_prefixes = ["www", "mail", "ftp", "admin", "dev", "api", "staging"]
            found = []
            
            for prefix in common_prefixes:
                subdomain = f"{prefix}.{target}"
                dns_result = await self._dns_lookup(subdomain)
                if dns_result.get("success") and dns_result.get("records"):
                    found.append(subdomain)
            
            return {
                "success": True,
                "subdomains": found,
                "count": len(found),
                "method": "basic"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _whois_lookup(self, target: str, **kwargs) -> Dict:
        """WHOIS lookup"""
        import subprocess
        
        try:
            result = subprocess.run(
                ["whois", target],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": True,
                "output": result.stdout[:2000],
                "parsed": self._parse_whois(result.stdout)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _tech_detect(self, target: str, **kwargs) -> Dict:
        """Technology detection"""
        import subprocess
        
        # Use whatweb if available
        try:
            url = target if target.startswith("http") else f"http://{target}"
            result = subprocess.run(
                ["whatweb", "-q", "--no-errors", url],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "success": True,
                "technologies": result.stdout,
                "url": url
            }
        except FileNotFoundError:
            # Fallback: basic HTTP headers check
            import httpx
            
            try:
                url = target if target.startswith("http") else f"http://{target}"
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(url)
                    
                    techs = []
                    headers = dict(response.headers)
                    
                    if "x-powered-by" in headers:
                        techs.append(headers["x-powered-by"])
                    if "server" in headers:
                        techs.append(headers["server"])
                    
                    return {
                        "success": True,
                        "technologies": techs,
                        "headers": headers,
                        "method": "basic"
                    }
            except:
                return {"success": False, "error": "Detection failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _port_scan(self, target: str, ports: str = "21-25,80,443,8080", **kwargs) -> Dict:
        """Quick port scan"""
        import subprocess
        
        try:
            result = subprocess.run(
                ["nmap", "-Pn", "-p", ports, "--open", target],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            open_ports = self._parse_nmap_ports(result.stdout)
            
            return {
                "success": True,
                "output": result.stdout,
                "open_ports": open_ports
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _osint_search(self, target: str, **kwargs) -> Dict:
        """OSINT search"""
        # Simulated - in production would use APIs
        return {
            "success": True,
            "sources_checked": ["dns", "whois", "ssl_certs"],
            "note": "Full OSINT requires API integrations"
        }
    
    # ============ Parsers ============
    
    def _parse_nslookup(self, output: str) -> List[str]:
        """Parse nslookup output"""
        records = []
        for line in output.split("\n"):
            if "Address:" in line and "#" not in line:
                addr = line.split("Address:")[-1].strip()
                if addr:
                    records.append(addr)
        return records
    
    def _parse_whois(self, output: str) -> Dict:
        """Parse WHOIS output"""
        info = {}
        key_fields = ["Registrar", "Creation Date", "Expiration Date", "Name Server"]
        
        for line in output.split("\n"):
            for field in key_fields:
                if field.lower() in line.lower():
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        info[field] = parts[1].strip()
        
        return info
    
    def _parse_nmap_ports(self, output: str) -> List[Dict]:
        """Parse nmap output for open ports"""
        ports = []
        for line in output.split("\n"):
            if "/tcp" in line or "/udp" in line:
                parts = line.split()
                if len(parts) >= 3 and "open" in parts[1]:
                    ports.append({
                        "port": parts[0].split("/")[0],
                        "protocol": parts[0].split("/")[1],
                        "service": parts[2] if len(parts) > 2 else "unknown"
                    })
        return ports
