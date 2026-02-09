"""
RedClaw Core - RAG System
Retrieval-Augmented Generation with security knowledge bases
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import hashlib

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


@dataclass
class RAGDocument:
    """Document in RAG system"""
    id: str
    content: str
    source: str  # cve, exploit, mitre, custom
    metadata: Dict


@dataclass
class RAGResult:
    """RAG search result"""
    document: RAGDocument
    score: float
    highlights: List[str] = None


class RAGSystem:
    """
    RAG System for Security Knowledge
    
    Knowledge bases:
    - CVE Database
    - ExploitDB
    - MITRE ATT&CK
    - Custom techniques
    """
    
    COLLECTIONS = {
        "cve": "redclaw_cve",
        "exploit": "redclaw_exploits",
        "mitre": "redclaw_mitre",
        "techniques": "redclaw_techniques"
    }
    
    def __init__(
        self,
        persist_dir: str = "./data/rag",
        auto_load: bool = True
    ):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        
        if CHROMA_AVAILABLE:
            self.client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            self._init_collections()
        else:
            self.client = None
            self._init_fallback()
        
        if auto_load:
            self._load_builtin_knowledge()
    
    def _init_collections(self):
        """Initialize ChromaDB collections"""
        self.collections = {}
        for name, collection_name in self.COLLECTIONS.items():
            self.collections[name] = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def _init_fallback(self):
        """Initialize fallback storage"""
        self.fallback_file = os.path.join(self.persist_dir, "rag.json")
        if os.path.exists(self.fallback_file):
            with open(self.fallback_file, "r") as f:
                self.fallback_data = json.load(f)
        else:
            self.fallback_data = {k: [] for k in self.COLLECTIONS}
    
    def _save_fallback(self):
        """Save fallback data"""
        if not CHROMA_AVAILABLE:
            with open(self.fallback_file, "w") as f:
                json.dump(self.fallback_data, f, indent=2)
    
    def _load_builtin_knowledge(self):
        """Load built-in security knowledge"""
        knowledge_dir = os.path.join(os.path.dirname(__file__), "..", "knowledge")
        
        # Load MITRE ATT&CK basics
        mitre_data = self._get_basic_mitre()
        for technique in mitre_data:
            self.add_document(
                collection="mitre",
                doc_id=technique["id"],
                content=f"{technique['name']}\n{technique['description']}",
                metadata=technique
            )
        
        # Load common exploit patterns
        exploits = self._get_common_exploits()
        for exploit in exploits:
            self.add_document(
                collection="exploit",
                doc_id=exploit["id"],
                content=f"{exploit['name']}\n{exploit['description']}",
                metadata=exploit
            )
    
    def _get_basic_mitre(self) -> List[Dict]:
        """Basic MITRE ATT&CK techniques"""
        return [
            {
                "id": "T1566",
                "name": "Phishing",
                "tactic": "initial-access",
                "description": "Adversaries may send phishing messages to gain access to victim systems."
            },
            {
                "id": "T1059",
                "name": "Command and Scripting Interpreter",
                "tactic": "execution",
                "description": "Adversaries may abuse command and script interpreters to execute commands."
            },
            {
                "id": "T1078",
                "name": "Valid Accounts",
                "tactic": "persistence",
                "description": "Adversaries may obtain and abuse credentials of existing accounts."
            },
            {
                "id": "T1548",
                "name": "Abuse Elevation Control Mechanism",
                "tactic": "privilege-escalation",
                "description": "Adversaries may circumvent mechanisms designed to control elevate privileges."
            },
            {
                "id": "T1070",
                "name": "Indicator Removal",
                "tactic": "defense-evasion",
                "description": "Adversaries may delete or modify artifacts to avoid detection."
            },
            {
                "id": "T1003",
                "name": "OS Credential Dumping",
                "tactic": "credential-access",
                "description": "Adversaries may attempt to dump credentials from the operating system."
            },
            {
                "id": "T1087",
                "name": "Account Discovery",
                "tactic": "discovery",
                "description": "Adversaries may attempt to get a listing of accounts on a system."
            },
            {
                "id": "T1021",
                "name": "Remote Services",
                "tactic": "lateral-movement",
                "description": "Adversaries may use remote services to move laterally."
            },
            {
                "id": "T1005",
                "name": "Data from Local System",
                "tactic": "collection",
                "description": "Adversaries may search local system sources for data of interest."
            },
            {
                "id": "T1048",
                "name": "Exfiltration Over Alternative Protocol",
                "tactic": "exfiltration",
                "description": "Adversaries may steal data by exfiltrating it over a different protocol."
            }
        ]
    
    def _get_common_exploits(self) -> List[Dict]:
        """Common exploit patterns"""
        return [
            {
                "id": "EXP001",
                "name": "SQL Injection",
                "type": "web",
                "description": "SQL injection attacks via user-supplied input to database queries.",
                "severity": "high"
            },
            {
                "id": "EXP002",
                "name": "XSS - Cross-Site Scripting",
                "type": "web",
                "description": "Injection of malicious scripts into web pages viewed by other users.",
                "severity": "medium"
            },
            {
                "id": "EXP003",
                "name": "Remote Code Execution",
                "type": "network",
                "description": "Vulnerabilities allowing execution of arbitrary code on remote systems.",
                "severity": "critical"
            },
            {
                "id": "EXP004",
                "name": "Path Traversal",
                "type": "web",
                "description": "Access to files outside the web root directory using ../ sequences.",
                "severity": "high"
            },
            {
                "id": "EXP005",
                "name": "Command Injection",
                "type": "web",
                "description": "Execution of arbitrary OS commands on the host server.",
                "severity": "critical"
            },
            {
                "id": "EXP006",
                "name": "Buffer Overflow",
                "type": "binary",
                "description": "Writing data beyond buffer boundaries to execute arbitrary code.",
                "severity": "critical"
            },
            {
                "id": "EXP007",
                "name": "SSRF - Server-Side Request Forgery",
                "type": "web",
                "description": "Force server to make requests to unintended locations.",
                "severity": "high"
            },
            {
                "id": "EXP008",
                "name": "Deserialization Attack",
                "type": "application",
                "description": "Exploit unsafe deserialization of user-controlled data.",
                "severity": "critical"
            }
        ]
    
    def add_document(
        self,
        collection: str,
        doc_id: str,
        content: str,
        metadata: Dict = None
    ) -> bool:
        """Add document to collection"""
        
        if collection not in self.COLLECTIONS:
            return False
        
        meta = metadata or {}
        meta["added_at"] = datetime.now().isoformat()
        
        if CHROMA_AVAILABLE:
            try:
                self.collections[collection].upsert(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[meta]
                )
                return True
            except Exception:
                return False
        else:
            # Fallback
            doc = {"id": doc_id, "content": content, "metadata": meta}
            # Update or add
            updated = False
            for i, d in enumerate(self.fallback_data[collection]):
                if d["id"] == doc_id:
                    self.fallback_data[collection][i] = doc
                    updated = True
                    break
            if not updated:
                self.fallback_data[collection].append(doc)
            self._save_fallback()
            return True
    
    def search(
        self,
        query: str,
        collections: List[str] = None,
        n_results: int = 5,
        filters: Dict = None
    ) -> List[RAGResult]:
        """Search across collections"""
        
        search_collections = collections or list(self.COLLECTIONS.keys())
        results = []
        
        for coll_name in search_collections:
            if coll_name not in self.COLLECTIONS:
                continue
            
            if CHROMA_AVAILABLE:
                try:
                    coll_results = self.collections[coll_name].query(
                        query_texts=[query],
                        n_results=n_results,
                        where=filters
                    )
                    
                    if coll_results["ids"]:
                        for i, doc_id in enumerate(coll_results["ids"][0]):
                            doc = RAGDocument(
                                id=doc_id,
                                content=coll_results["documents"][0][i],
                                source=coll_name,
                                metadata=coll_results["metadatas"][0][i]
                            )
                            score = 1.0 - (coll_results["distances"][0][i] if coll_results["distances"] else 0)
                            results.append(RAGResult(document=doc, score=score))
                except Exception:
                    pass
            else:
                # Fallback search
                query_lower = query.lower()
                for doc in self.fallback_data.get(coll_name, []):
                    if query_lower in doc["content"].lower():
                        results.append(RAGResult(
                            document=RAGDocument(
                                id=doc["id"],
                                content=doc["content"],
                                source=coll_name,
                                metadata=doc["metadata"]
                            ),
                            score=0.8
                        ))
        
        # Sort by score and limit
        results.sort(key=lambda r: -r.score)
        return results[:n_results]
    
    def get_context_for_target(
        self,
        target_type: str,
        technologies: List[str] = None
    ) -> str:
        """Get relevant context for LLM based on target"""
        
        # Search for relevant techniques
        technique_results = self.search(
            target_type,
            collections=["mitre", "exploit"],
            n_results=5
        )
        
        if technologies:
            for tech in technologies:
                tech_results = self.search(tech, n_results=3)
                technique_results.extend(tech_results)
        
        # Format as context
        context_parts = []
        seen = set()
        
        for result in technique_results:
            if result.document.id in seen:
                continue
            seen.add(result.document.id)
            
            context_parts.append(f"""
### {result.document.metadata.get('name', result.document.id)}
Source: {result.document.source.upper()}
{result.document.content[:500]}
""")
        
        return "\n".join(context_parts[:10])
    
    def search_cve(
        self,
        query: str,
        n_results: int = 5
    ) -> List[RAGResult]:
        """Search CVE database"""
        return self.search(query, collections=["cve"], n_results=n_results)
    
    def search_exploits(
        self,
        query: str,
        exploit_type: str = None,
        n_results: int = 5
    ) -> List[RAGResult]:
        """Search exploit database"""
        filters = {"type": exploit_type} if exploit_type else None
        return self.search(query, collections=["exploit"], n_results=n_results, filters=filters)
    
    def search_mitre(
        self,
        query: str,
        tactic: str = None,
        n_results: int = 5
    ) -> List[RAGResult]:
        """Search MITRE ATT&CK"""
        filters = {"tactic": tactic} if tactic else None
        return self.search(query, collections=["mitre"], n_results=n_results, filters=filters)
    
    def import_cve_data(self, cve_file: str) -> int:
        """Import CVE data from JSON file"""
        if not os.path.exists(cve_file):
            return 0
        
        count = 0
        with open(cve_file, "r") as f:
            data = json.load(f)
        
        cves = data if isinstance(data, list) else data.get("CVE_Items", [])
        
        for cve in cves:
            cve_id = cve.get("cve", {}).get("CVE_data_meta", {}).get("ID", "")
            if not cve_id:
                continue
            
            desc = ""
            desc_data = cve.get("cve", {}).get("description", {}).get("description_data", [])
            if desc_data:
                desc = desc_data[0].get("value", "")
            
            self.add_document(
                collection="cve",
                doc_id=cve_id,
                content=f"{cve_id}\n{desc}",
                metadata={
                    "cve_id": cve_id,
                    "description": desc,
                    "published": cve.get("publishedDate", "")
                }
            )
            count += 1
        
        return count
    
    def get_stats(self) -> Dict:
        """Get RAG system statistics"""
        if CHROMA_AVAILABLE:
            return {
                "cve_count": self.collections["cve"].count(),
                "exploit_count": self.collections["exploit"].count(),
                "mitre_count": self.collections["mitre"].count(),
                "techniques_count": self.collections["techniques"].count(),
                "using_chromadb": True
            }
        else:
            return {
                "cve_count": len(self.fallback_data.get("cve", [])),
                "exploit_count": len(self.fallback_data.get("exploit", [])),
                "mitre_count": len(self.fallback_data.get("mitre", [])),
                "techniques_count": len(self.fallback_data.get("techniques", [])),
                "using_chromadb": False
            }
