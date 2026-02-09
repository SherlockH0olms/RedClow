"""
RedClaw Core - Memory Manager
Persistent memory with ChromaDB for context retention
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
import hashlib

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


@dataclass
class MemoryEntry:
    """Single memory entry"""
    id: str
    type: str  # finding, command, pattern, context
    content: str
    metadata: Dict = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: Optional[str] = None


@dataclass 
class AttackPattern:
    """Learned attack pattern"""
    id: str
    name: str
    description: str
    target_type: str
    tools: List[str]
    success_rate: float = 0.0
    usage_count: int = 0
    last_used: Optional[str] = None


class MemoryManager:
    """
    Memory Manager with ChromaDB
    
    Features:
    - Semantic search over past findings
    - Attack pattern learning
    - Session persistence
    - Context injection for LLM
    """
    
    COLLECTION_NAMES = {
        "findings": "redclaw_findings",
        "patterns": "redclaw_patterns",
        "context": "redclaw_context",
        "sessions": "redclaw_sessions"
    }
    
    def __init__(
        self,
        persist_dir: str = "./data/memory",
        session_id: Optional[str] = None
    ):
        self.persist_dir = persist_dir
        self.session_id = session_id or self._generate_session_id()
        
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize ChromaDB
        if CHROMA_AVAILABLE:
            self.client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            self._init_collections()
        else:
            self.client = None
            self._init_fallback()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        ts = datetime.now().isoformat()
        return hashlib.md5(ts.encode()).hexdigest()[:12]
    
    def _init_collections(self):
        """Initialize ChromaDB collections"""
        self.collections = {}
        for name, collection_name in self.COLLECTION_NAMES.items():
            self.collections[name] = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def _init_fallback(self):
        """Initialize JSON fallback storage"""
        self.fallback_file = os.path.join(self.persist_dir, "memory.json")
        if os.path.exists(self.fallback_file):
            with open(self.fallback_file, "r") as f:
                self.fallback_data = json.load(f)
        else:
            self.fallback_data = {
                "findings": [],
                "patterns": [],
                "context": [],
                "sessions": []
            }
    
    def _save_fallback(self):
        """Save fallback data to disk"""
        if not CHROMA_AVAILABLE:
            with open(self.fallback_file, "w") as f:
                json.dump(self.fallback_data, f, indent=2)
    
    # ==================== Findings ====================
    
    def add_finding(
        self,
        finding_type: str,
        title: str,
        description: str,
        severity: str,
        target: str,
        evidence: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Add security finding to memory"""
        
        finding_id = hashlib.md5(
            f"{title}{target}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        content = f"{title}\n{description}\n{evidence or ''}"
        meta = {
            "type": finding_type,
            "title": title,
            "severity": severity,
            "target": target,
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        if CHROMA_AVAILABLE:
            self.collections["findings"].add(
                ids=[finding_id],
                documents=[content],
                metadatas=[meta]
            )
        else:
            self.fallback_data["findings"].append({
                "id": finding_id,
                "content": content,
                "metadata": meta
            })
            self._save_fallback()
        
        return finding_id
    
    def search_findings(
        self,
        query: str,
        n_results: int = 10,
        severity: Optional[str] = None,
        target: Optional[str] = None
    ) -> List[Dict]:
        """Search findings by semantic similarity"""
        
        if CHROMA_AVAILABLE:
            where = {}
            if severity:
                where["severity"] = severity
            if target:
                where["target"] = target
            
            results = self.collections["findings"].query(
                query_texts=[query],
                n_results=n_results,
                where=where if where else None
            )
            
            findings = []
            if results["ids"]:
                for i, doc_id in enumerate(results["ids"][0]):
                    findings.append({
                        "id": doc_id,
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None
                    })
            return findings
        else:
            # Fallback: simple substring search
            query_lower = query.lower()
            matches = []
            for f in self.fallback_data["findings"]:
                if query_lower in f["content"].lower():
                    if severity and f["metadata"].get("severity") != severity:
                        continue
                    if target and f["metadata"].get("target") != target:
                        continue
                    matches.append(f)
            return matches[:n_results]
    
    def get_findings_for_target(self, target: str) -> List[Dict]:
        """Get all findings for a target"""
        return self.search_findings("", n_results=100, target=target)
    
    # ==================== Attack Patterns ====================
    
    def add_pattern(self, pattern: AttackPattern) -> str:
        """Add or update attack pattern"""
        
        pattern_dict = asdict(pattern)
        content = f"{pattern.name}\n{pattern.description}"
        
        if CHROMA_AVAILABLE:
            # Check if exists
            existing = self.collections["patterns"].get(ids=[pattern.id])
            if existing["ids"]:
                self.collections["patterns"].update(
                    ids=[pattern.id],
                    documents=[content],
                    metadatas=[pattern_dict]
                )
            else:
                self.collections["patterns"].add(
                    ids=[pattern.id],
                    documents=[content],
                    metadatas=[pattern_dict]
                )
        else:
            # Update or add in fallback
            updated = False
            for i, p in enumerate(self.fallback_data["patterns"]):
                if p["id"] == pattern.id:
                    self.fallback_data["patterns"][i] = {
                        "id": pattern.id,
                        "content": content,
                        "metadata": pattern_dict
                    }
                    updated = True
                    break
            if not updated:
                self.fallback_data["patterns"].append({
                    "id": pattern.id,
                    "content": content,
                    "metadata": pattern_dict
                })
            self._save_fallback()
        
        return pattern.id
    
    def get_patterns_for_target(
        self,
        target_type: str,
        n_results: int = 5
    ) -> List[AttackPattern]:
        """Get relevant attack patterns for target type"""
        
        if CHROMA_AVAILABLE:
            results = self.collections["patterns"].query(
                query_texts=[target_type],
                n_results=n_results,
                where={"target_type": target_type}
            )
            
            patterns = []
            if results["metadatas"]:
                for meta in results["metadatas"][0]:
                    patterns.append(AttackPattern(**meta))
            return sorted(patterns, key=lambda p: -p.success_rate)
        else:
            matches = [
                AttackPattern(**p["metadata"])
                for p in self.fallback_data["patterns"]
                if p["metadata"].get("target_type") == target_type
            ]
            return sorted(matches, key=lambda p: -p.success_rate)[:n_results]
    
    def update_pattern_stats(
        self,
        pattern_id: str,
        success: bool
    ):
        """Update pattern usage statistics"""
        
        if CHROMA_AVAILABLE:
            existing = self.collections["patterns"].get(ids=[pattern_id])
            if existing["metadatas"]:
                meta = existing["metadatas"][0]
                meta["usage_count"] = meta.get("usage_count", 0) + 1
                if success:
                    # Update success rate with running average
                    rate = meta.get("success_rate", 0.0)
                    count = meta["usage_count"]
                    meta["success_rate"] = ((rate * (count - 1)) + 1.0) / count
                else:
                    rate = meta.get("success_rate", 0.0)
                    count = meta["usage_count"]
                    meta["success_rate"] = (rate * (count - 1)) / count
                meta["last_used"] = datetime.now().isoformat()
                
                self.collections["patterns"].update(
                    ids=[pattern_id],
                    metadatas=[meta]
                )
    
    # ==================== Context ====================
    
    def add_context(
        self,
        context_type: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Add context entry"""
        
        context_id = hashlib.md5(
            f"{context_type}{content[:50]}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        meta = {
            "type": context_type,
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        if CHROMA_AVAILABLE:
            self.collections["context"].add(
                ids=[context_id],
                documents=[content],
                metadatas=[meta]
            )
        else:
            self.fallback_data["context"].append({
                "id": context_id,
                "content": content,
                "metadata": meta
            })
            self._save_fallback()
        
        return context_id
    
    def get_relevant_context(
        self,
        query: str,
        n_results: int = 5
    ) -> List[str]:
        """Get relevant context for LLM injection"""
        
        if CHROMA_AVAILABLE:
            results = self.collections["context"].query(
                query_texts=[query],
                n_results=n_results
            )
            return results["documents"][0] if results["documents"] else []
        else:
            query_lower = query.lower()
            matches = [
                c["content"] for c in self.fallback_data["context"]
                if query_lower in c["content"].lower()
            ]
            return matches[:n_results]
    
    # ==================== Sessions ====================
    
    def save_session(
        self,
        target: str,
        phase: str,
        state: Dict
    ) -> str:
        """Save session state"""
        
        session_data = {
            "session_id": self.session_id,
            "target": target,
            "phase": phase,
            "state": state,
            "saved_at": datetime.now().isoformat()
        }
        
        if CHROMA_AVAILABLE:
            self.collections["sessions"].upsert(
                ids=[self.session_id],
                documents=[json.dumps(session_data)],
                metadatas={"target": target, "phase": phase}
            )
        else:
            # Update or add
            updated = False
            for i, s in enumerate(self.fallback_data["sessions"]):
                if s.get("session_id") == self.session_id:
                    self.fallback_data["sessions"][i] = session_data
                    updated = True
                    break
            if not updated:
                self.fallback_data["sessions"].append(session_data)
            self._save_fallback()
        
        return self.session_id
    
    def load_session(self, session_id: str) -> Optional[Dict]:
        """Load session state"""
        
        if CHROMA_AVAILABLE:
            results = self.collections["sessions"].get(ids=[session_id])
            if results["documents"]:
                return json.loads(results["documents"][0])
            return None
        else:
            for s in self.fallback_data["sessions"]:
                if s.get("session_id") == session_id:
                    return s
            return None
    
    def list_sessions(self) -> List[Dict]:
        """List all sessions"""
        
        if CHROMA_AVAILABLE:
            results = self.collections["sessions"].get()
            sessions = []
            for i, doc in enumerate(results["documents"] or []):
                try:
                    data = json.loads(doc)
                    sessions.append({
                        "session_id": results["ids"][i],
                        "target": data.get("target", "unknown"),
                        "phase": data.get("phase", "unknown"),
                        "saved_at": data.get("saved_at", "unknown")
                    })
                except:
                    pass
            return sessions
        else:
            return [
                {
                    "session_id": s.get("session_id"),
                    "target": s.get("target"),
                    "phase": s.get("phase"),
                    "saved_at": s.get("saved_at")
                }
                for s in self.fallback_data["sessions"]
            ]
    
    # ==================== Export ====================
    
    def export_session_data(self) -> Dict:
        """Export all data for current session"""
        
        findings = self.search_findings("", n_results=1000)
        session_findings = [
            f for f in findings
            if f.get("metadata", {}).get("session_id") == self.session_id
        ]
        
        return {
            "session_id": self.session_id,
            "findings": session_findings,
            "exported_at": datetime.now().isoformat()
        }
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        
        if CHROMA_AVAILABLE:
            return {
                "findings_count": self.collections["findings"].count(),
                "patterns_count": self.collections["patterns"].count(),
                "context_count": self.collections["context"].count(),
                "sessions_count": self.collections["sessions"].count(),
                "current_session": self.session_id,
                "using_chromadb": True
            }
        else:
            return {
                "findings_count": len(self.fallback_data["findings"]),
                "patterns_count": len(self.fallback_data["patterns"]),
                "context_count": len(self.fallback_data["context"]),
                "sessions_count": len(self.fallback_data["sessions"]),
                "current_session": self.session_id,
                "using_chromadb": False
            }
