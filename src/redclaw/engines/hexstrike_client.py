"""
RedClaw Engines - HexStrike Client
HexStrike-AI Integration for Combined Offensive Operations
"""

import asyncio
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ScanType(Enum):
    """Scan types"""
    PORT = "port"
    VULN = "vulnerability"
    WEB = "web"
    NETWORK = "network"
    FULL = "full"


class AttackType(Enum):
    """Attack types"""
    EXPLOIT = "exploit"
    BRUTEFORCE = "bruteforce"
    INJECTION = "injection"
    PHISHING = "phishing"
    DDOS = "ddos"


@dataclass
class ScanResult:
    """Scan result"""
    scan_id: str
    target: str
    scan_type: ScanType
    status: str
    findings: List[Dict] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class AttackResult:
    """Attack result"""
    attack_id: str
    target: str
    attack_type: AttackType
    success: bool
    output: str
    evidence: Dict = field(default_factory=dict)


class HexStrikeClient:
    """
    HexStrike-AI Client
    
    Integration with HexStrike for:
    - Automated vulnerability scanning
    - Intelligent exploit selection
    - Coordinated attack campaigns
    - Result aggregation
    
    HexStrike provides an AI-enhanced layer over
    traditional security tools.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:9999",
        api_key: str = None
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=120.0
        )
        
        # Cache
        self.active_scans: Dict[str, ScanResult] = {}
        self.active_attacks: Dict[str, AttackResult] = {}
    
    async def health_check(self) -> bool:
        """Check HexStrike availability"""
        try:
            response = await self.client.get("/api/health")
            return response.status_code == 200
        except:
            return False
    
    # ============ Scanning ============
    
    async def start_scan(
        self,
        target: str,
        scan_type: ScanType = ScanType.FULL,
        options: Dict = None
    ) -> ScanResult:
        """Start vulnerability scan"""
        try:
            payload = {
                "target": target,
                "scan_type": scan_type.value,
                "options": options or {}
            }
            
            response = await self.client.post("/api/scan/start", json=payload)
            data = response.json()
            
            scan = ScanResult(
                scan_id=data.get("scan_id", ""),
                target=target,
                scan_type=scan_type,
                status="running"
            )
            
            self.active_scans[scan.scan_id] = scan
            return scan
            
        except Exception as e:
            return ScanResult(
                scan_id="error",
                target=target,
                scan_type=scan_type,
                status=f"error: {str(e)}"
            )
    
    async def get_scan_status(self, scan_id: str) -> ScanResult:
        """Get scan status"""
        try:
            response = await self.client.get(f"/api/scan/{scan_id}/status")
            data = response.json()
            
            scan = self.active_scans.get(scan_id)
            if scan:
                scan.status = data.get("status", "unknown")
                scan.findings = data.get("findings", [])
                if data.get("completed_at"):
                    scan.completed_at = datetime.fromisoformat(data["completed_at"])
            
            return scan or ScanResult(
                scan_id=scan_id,
                target="",
                scan_type=ScanType.FULL,
                status=data.get("status", "unknown"),
                findings=data.get("findings", [])
            )
            
        except Exception as e:
            return ScanResult(
                scan_id=scan_id,
                target="",
                scan_type=ScanType.FULL,
                status=f"error: {str(e)}"
            )
    
    async def wait_for_scan(
        self,
        scan_id: str,
        timeout: int = 300
    ) -> ScanResult:
        """Wait for scan completion"""
        start = datetime.now()
        
        while (datetime.now() - start).seconds < timeout:
            result = await self.get_scan_status(scan_id)
            
            if result.status in ["completed", "failed", "error"]:
                return result
            
            await asyncio.sleep(5)
        
        result = await self.get_scan_status(scan_id)
        result.status = "timeout"
        return result
    
    async def stop_scan(self, scan_id: str) -> bool:
        """Stop running scan"""
        try:
            response = await self.client.post(f"/api/scan/{scan_id}/stop")
            return response.status_code == 200
        except:
            return False
    
    # ============ Attacks ============
    
    async def launch_attack(
        self,
        target: str,
        attack_type: AttackType,
        options: Dict = None
    ) -> AttackResult:
        """Launch attack"""
        try:
            payload = {
                "target": target,
                "attack_type": attack_type.value,
                "options": options or {}
            }
            
            response = await self.client.post("/api/attack/launch", json=payload)
            data = response.json()
            
            result = AttackResult(
                attack_id=data.get("attack_id", ""),
                target=target,
                attack_type=attack_type,
                success=data.get("success", False),
                output=data.get("output", ""),
                evidence=data.get("evidence", {})
            )
            
            self.active_attacks[result.attack_id] = result
            return result
            
        except Exception as e:
            return AttackResult(
                attack_id="error",
                target=target,
                attack_type=attack_type,
                success=False,
                output=str(e)
            )
    
    async def get_attack_status(self, attack_id: str) -> Dict:
        """Get attack status"""
        try:
            response = await self.client.get(f"/api/attack/{attack_id}/status")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    # ============ Intelligence ============
    
    async def analyze_target(self, target: str) -> Dict:
        """AI-powered target analysis"""
        try:
            response = await self.client.post(
                "/api/intel/analyze",
                json={"target": target}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def recommend_attacks(
        self,
        target: str,
        vulnerabilities: List[Dict] = None
    ) -> List[Dict]:
        """Get AI attack recommendations"""
        try:
            response = await self.client.post(
                "/api/intel/recommend",
                json={
                    "target": target,
                    "vulnerabilities": vulnerabilities or []
                }
            )
            return response.json().get("recommendations", [])
        except:
            return []
    
    async def prioritize_vulnerabilities(
        self,
        vulnerabilities: List[Dict]
    ) -> List[Dict]:
        """Prioritize vulnerabilities by exploitability"""
        try:
            response = await self.client.post(
                "/api/intel/prioritize",
                json={"vulnerabilities": vulnerabilities}
            )
            return response.json().get("prioritized", vulnerabilities)
        except:
            return vulnerabilities
    
    # ============ Tools ============
    
    async def run_nmap(
        self,
        target: str,
        options: str = "-sV -sC"
    ) -> Dict:
        """Run Nmap scan"""
        try:
            response = await self.client.post(
                "/api/tools/nmap",
                json={"target": target, "options": options}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def run_nikto(
        self,
        target: str,
        options: Dict = None
    ) -> Dict:
        """Run Nikto web scan"""
        try:
            response = await self.client.post(
                "/api/tools/nikto",
                json={"target": target, "options": options or {}}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def run_sqlmap(
        self,
        url: str,
        options: Dict = None
    ) -> Dict:
        """Run SQLMap"""
        try:
            response = await self.client.post(
                "/api/tools/sqlmap",
                json={"url": url, "options": options or {}}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def run_hydra(
        self,
        target: str,
        service: str,
        options: Dict = None
    ) -> Dict:
        """Run Hydra bruteforce"""
        try:
            response = await self.client.post(
                "/api/tools/hydra",
                json={
                    "target": target,
                    "service": service,
                    "options": options or {}
                }
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    # ============ Campaigns ============
    
    async def create_campaign(
        self,
        name: str,
        targets: List[str],
        objectives: List[str]
    ) -> Dict:
        """Create attack campaign"""
        try:
            response = await self.client.post(
                "/api/campaign/create",
                json={
                    "name": name,
                    "targets": targets,
                    "objectives": objectives
                }
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def run_campaign(self, campaign_id: str) -> Dict:
        """Run campaign"""
        try:
            response = await self.client.post(
                f"/api/campaign/{campaign_id}/run"
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def get_campaign_status(self, campaign_id: str) -> Dict:
        """Get campaign status"""
        try:
            response = await self.client.get(
                f"/api/campaign/{campaign_id}/status"
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    # ============ Reporting ============
    
    async def generate_report(
        self,
        scan_ids: List[str] = None,
        attack_ids: List[str] = None,
        format: str = "json"
    ) -> Dict:
        """Generate combined report"""
        try:
            response = await self.client.post(
                "/api/report/generate",
                json={
                    "scan_ids": scan_ids or [],
                    "attack_ids": attack_ids or [],
                    "format": format
                }
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        """Close client"""
        await self.client.aclose()


# Fallback implementation when HexStrike is not available
class HexStrikeFallback:
    """
    Fallback implementation using local tools
    when HexStrike server is unavailable
    """
    
    def __init__(self):
        self.scans: Dict[str, Dict] = {}
        self.attacks: Dict[str, Dict] = {}
    
    async def health_check(self) -> bool:
        return True  # Fallback always "available"
    
    async def run_nmap_local(
        self,
        target: str,
        options: str = "-sV"
    ) -> Dict:
        """Run nmap locally"""
        import subprocess
        
        try:
            cmd = f"nmap {options} {target}"
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def run_nikto_local(
        self,
        target: str
    ) -> Dict:
        """Run nikto locally"""
        import subprocess
        
        try:
            cmd = f"nikto -h {target}"
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                timeout=600
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}
