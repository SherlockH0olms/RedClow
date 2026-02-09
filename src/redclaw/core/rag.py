"""
RedClaw - RAG (Retrieval-Augmented Generation) System
CVE database, exploit database, attack patterns
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import os

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


@dataclass
class CVEEntry:
    """CVE database entry"""
    cve_id: str
    description: str
    severity: str
    cvss_score: float
    affected_products: List[str]
    references: List[str]
    exploit_available: bool = False


@dataclass
class ExploitEntry:
    """Exploit database entry"""
    exploit_id: str
    title: str
    type: str  # remote, local, web, dos
    platform: str
    author: str
    date: str
    cve: Optional[str]
    path: str


@dataclass
class AttackTechnique:
    """MITRE ATT&CK technique"""
    technique_id: str
    name: str
    tactic: str
    description: str
    detection: str
    mitigations: List[str]


class RAGSystem:
    """
    Retrieval-Augmented Generation System
    
    Knowledge bases:
    - CVE database
    - ExploitDB
    - MITRE ATT&CK
    - Custom attack patterns
    
    Features:
    - Semantic search with embeddings
    - Context retrieval for LLM prompts
    - Auto-update from online sources
    """
    
    def __init__(self, data_dir: str = "./data/rag"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory caches
        self.cve_cache: Dict[str, CVEEntry] = {}
        self.exploit_cache: Dict[str, ExploitEntry] = {}
        self.technique_cache: Dict[str, AttackTechnique] = {}
        
        # Embedding model
        self.embedder = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception:
                pass
        
        # ChromaDB collections
        self.chroma_client = None
        self.cve_collection = None
        self.exploit_collection = None
        self.technique_collection = None
        
        if CHROMA_AVAILABLE:
            self._init_chromadb()
        
        # Load local data
        self._load_local_data()
    
    def _init_chromadb(self):
        """Initialize ChromaDB collections"""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.data_dir / "chroma")
            )
            
            self.cve_collection = self.chroma_client.get_or_create_collection(
                name="cve_database"
            )
            self.exploit_collection = self.chroma_client.get_or_create_collection(
                name="exploit_database"
            )
            self.technique_collection = self.chroma_client.get_or_create_collection(
                name="attack_techniques"
            )
        except Exception as e:
            print(f"ChromaDB init failed: {e}")
    
    def _load_local_data(self):
        """Load data from local JSON files"""
        # Load CVEs
        cve_file = self.data_dir / "cve_cache.json"
        if cve_file.exists():
            with open(cve_file) as f:
                data = json.load(f)
                for cve_data in data:
                    cve = CVEEntry(**cve_data)
                    self.cve_cache[cve.cve_id] = cve
        
        # Load exploits
        exploit_file = self.data_dir / "exploit_cache.json"
        if exploit_file.exists():
            with open(exploit_file) as f:
                data = json.load(f)
                for exp_data in data:
                    exp = ExploitEntry(**exp_data)
                    self.exploit_cache[exp.exploit_id] = exp
        
        # Load techniques
        technique_file = self.data_dir / "technique_cache.json"
        if technique_file.exists():
            with open(technique_file) as f:
                data = json.load(f)
                for tech_data in data:
                    tech = AttackTechnique(**tech_data)
                    self.technique_cache[tech.technique_id] = tech
    
    def _save_local_data(self):
        """Save data to local JSON files"""
        # Save CVEs
        cve_data = [
            {
                "cve_id": c.cve_id,
                "description": c.description,
                "severity": c.severity,
                "cvss_score": c.cvss_score,
                "affected_products": c.affected_products,
                "references": c.references,
                "exploit_available": c.exploit_available
            }
            for c in self.cve_cache.values()
        ]
        with open(self.data_dir / "cve_cache.json", 'w') as f:
            json.dump(cve_data, f, indent=2)
        
        # Save exploits
        exploit_data = [
            {
                "exploit_id": e.exploit_id,
                "title": e.title,
                "type": e.type,
                "platform": e.platform,
                "author": e.author,
                "date": e.date,
                "cve": e.cve,
                "path": e.path
            }
            for e in self.exploit_cache.values()
        ]
        with open(self.data_dir / "exploit_cache.json", 'w') as f:
            json.dump(exploit_data, f, indent=2)
    
    def add_cve(self, cve: CVEEntry):
        """Add CVE to database"""
        self.cve_cache[cve.cve_id] = cve
        
        if self.cve_collection:
            doc = f"{cve.cve_id}: {cve.description}"
            self.cve_collection.add(
                documents=[doc],
                metadatas=[{
                    "severity": cve.severity,
                    "cvss": str(cve.cvss_score),
                    "exploit_available": str(cve.exploit_available)
                }],
                ids=[cve.cve_id]
            )
    
    def add_exploit(self, exploit: ExploitEntry):
        """Add exploit to database"""
        self.exploit_cache[exploit.exploit_id] = exploit
        
        if self.exploit_collection:
            doc = f"{exploit.title} ({exploit.type}, {exploit.platform})"
            self.exploit_collection.add(
                documents=[doc],
                metadatas=[{
                    "type": exploit.type,
                    "platform": exploit.platform,
                    "cve": exploit.cve or ""
                }],
                ids=[exploit.exploit_id]
            )
    
    def search_cve(
        self,
        query: str,
        n_results: int = 5,
        min_cvss: float = None
    ) -> List[CVEEntry]:
        """Search CVE database"""
        if self.cve_collection:
            results = self.cve_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            cves = []
            for cve_id in results['ids'][0]:
                if cve_id in self.cve_cache:
                    cve = self.cve_cache[cve_id]
                    if min_cvss is None or cve.cvss_score >= min_cvss:
                        cves.append(cve)
            return cves
        
        # Fallback: simple search
        query_lower = query.lower()
        matches = [
            c for c in self.cve_cache.values()
            if query_lower in c.description.lower() or query_lower in c.cve_id.lower()
        ]
        
        if min_cvss:
            matches = [c for c in matches if c.cvss_score >= min_cvss]
        
        return matches[:n_results]
    
    def search_exploits(
        self,
        query: str,
        n_results: int = 5,
        exploit_type: str = None,
        platform: str = None
    ) -> List[ExploitEntry]:
        """Search exploit database"""
        if self.exploit_collection:
            where_filter = {}
            if exploit_type:
                where_filter["type"] = exploit_type
            if platform:
                where_filter["platform"] = platform
            
            results = self.exploit_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter if where_filter else None
            )
            
            exploits = []
            for exp_id in results['ids'][0]:
                if exp_id in self.exploit_cache:
                    exploits.append(self.exploit_cache[exp_id])
            return exploits
        
        # Fallback
        query_lower = query.lower()
        matches = [
            e for e in self.exploit_cache.values()
            if query_lower in e.title.lower()
        ]
        
        if exploit_type:
            matches = [e for e in matches if e.type == exploit_type]
        if platform:
            matches = [e for e in matches if platform in e.platform.lower()]
        
        return matches[:n_results]
    
    def search_techniques(
        self,
        query: str,
        n_results: int = 5,
        tactic: str = None
    ) -> List[AttackTechnique]:
        """Search MITRE ATT&CK techniques"""
        if self.technique_collection:
            where_filter = {"tactic": tactic} if tactic else None
            
            results = self.technique_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            techniques = []
            for tech_id in results['ids'][0]:
                if tech_id in self.technique_cache:
                    techniques.append(self.technique_cache[tech_id])
            return techniques
        
        # Fallback
        query_lower = query.lower()
        matches = [
            t for t in self.technique_cache.values()
            if query_lower in t.name.lower() or query_lower in t.description.lower()
        ]
        
        if tactic:
            matches = [t for t in matches if t.tactic == tactic]
        
        return matches[:n_results]
    
    def get_context_for_service(
        self,
        service: str,
        version: str = ""
    ) -> str:
        """Get RAG context for a service"""
        query = f"{service} {version}".strip()
        
        context_parts = []
        
        # Search CVEs
        cves = self.search_cve(query, n_results=3)
        if cves:
            context_parts.append("**Known CVEs:**")
            for cve in cves:
                context_parts.append(
                    f"- {cve.cve_id} (CVSS: {cve.cvss_score}): {cve.description[:200]}"
                )
        
        # Search exploits
        exploits = self.search_exploits(query, n_results=3)
        if exploits:
            context_parts.append("\n**Available Exploits:**")
            for exp in exploits:
                context_parts.append(f"- {exp.title} ({exp.type})")
        
        return "\n".join(context_parts)
    
    def get_attack_context(
        self,
        phase: str,
        target_info: Dict
    ) -> str:
        """Get RAG context for attack phase"""
        context_parts = []
        
        # Map phase to MITRE tactics
        phase_to_tactic = {
            "reconnaissance": "reconnaissance",
            "scanning": "discovery",
            "exploitation": "initial-access",
            "post_exploitation": "persistence",
            "lateral_movement": "lateral-movement"
        }
        
        tactic = phase_to_tactic.get(phase)
        if tactic:
            techniques = self.search_techniques("", n_results=5, tactic=tactic)
            if techniques:
                context_parts.append(f"**{tactic.upper()} Techniques:**")
                for tech in techniques:
                    context_parts.append(f"- {tech.technique_id}: {tech.name}")
        
        # Add service-specific context
        services = target_info.get("services", [])
        for svc in services[:3]:
            svc_context = self.get_context_for_service(
                svc.get("service", ""),
                svc.get("version", "")
            )
            if svc_context:
                context_parts.append(f"\n**{svc.get('service', 'Service')}:**")
                context_parts.append(svc_context)
        
        return "\n".join(context_parts)
    
    async def update_from_nvd(self, api_key: str = None):
        """Update CVE database from NVD"""
        # NVD API integration would go here
        # For now, just log
        print("NVD update would be performed here")
    
    async def update_from_exploitdb(self):
        """Update exploit database from ExploitDB"""
        # ExploitDB integration would go here
        print("ExploitDB update would be performed here")


# Singleton
_rag_system: Optional[RAGSystem] = None


def get_rag_system(data_dir: str = None) -> RAGSystem:
    """Get RAG system instance"""
    global _rag_system
    
    if _rag_system is None:
        data_dir = data_dir or os.getenv("WORKSPACE_PATH", "./data/rag")
        _rag_system = RAGSystem(data_dir)
    
    return _rag_system
