"""
RedClaw - Memory and Context Manager
Vector database, attack history, pattern learning
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import hashlib
import os

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


@dataclass
class MemoryEntry:
    """Memory entry for attack context"""
    id: str
    entry_type: str  # finding, tool_output, decision, pattern
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AttackPattern:
    """Learned attack pattern"""
    pattern_id: str
    name: str
    services: List[str]
    techniques: List[str]
    success_rate: float
    last_used: datetime
    notes: str = ""


class MemoryManager:
    """
    Memory & Context Manager
    
    Capabilities:
    - Vector storage for semantic search (ChromaDB)
    - Attack history tracking
    - Pattern learning and retrieval
    - Target fingerprint database
    - Session persistence
    """
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage
        self.short_term: List[MemoryEntry] = []
        self.patterns: Dict[str, AttackPattern] = {}
        self.target_fingerprints: Dict[str, Dict] = {}
        
        # Vector database (if available)
        self.chroma_client = None
        self.collection = None
        
        if CHROMA_AVAILABLE:
            self._init_chromadb()
        
        # Load persistent data
        self._load_patterns()
        self._load_fingerprints()
    
    def _init_chromadb(self):
        """Initialize ChromaDB"""
        try:
            self.chroma_client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.data_dir / "chroma"),
                anonymized_telemetry=False
            ))
            self.collection = self.chroma_client.get_or_create_collection(
                name="redclaw_memory",
                metadata={"description": "RedClaw attack memory"}
            )
        except Exception as e:
            print(f"ChromaDB init failed: {e}")
            self.chroma_client = None
    
    def _load_patterns(self):
        """Load attack patterns from disk"""
        patterns_file = self.data_dir / "patterns.json"
        if patterns_file.exists():
            with open(patterns_file) as f:
                data = json.load(f)
                for p in data:
                    pattern = AttackPattern(
                        pattern_id=p["pattern_id"],
                        name=p["name"],
                        services=p["services"],
                        techniques=p["techniques"],
                        success_rate=p["success_rate"],
                        last_used=datetime.fromisoformat(p["last_used"]),
                        notes=p.get("notes", "")
                    )
                    self.patterns[pattern.pattern_id] = pattern
    
    def _save_patterns(self):
        """Save patterns to disk"""
        patterns_file = self.data_dir / "patterns.json"
        data = [
            {
                "pattern_id": p.pattern_id,
                "name": p.name,
                "services": p.services,
                "techniques": p.techniques,
                "success_rate": p.success_rate,
                "last_used": p.last_used.isoformat(),
                "notes": p.notes
            }
            for p in self.patterns.values()
        ]
        with open(patterns_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_fingerprints(self):
        """Load target fingerprints"""
        fp_file = self.data_dir / "fingerprints.json"
        if fp_file.exists():
            with open(fp_file) as f:
                self.target_fingerprints = json.load(f)
    
    def _save_fingerprints(self):
        """Save target fingerprints"""
        fp_file = self.data_dir / "fingerprints.json"
        with open(fp_file, 'w') as f:
            json.dump(self.target_fingerprints, f, indent=2)
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID"""
        return hashlib.md5(
            f"{content}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
    
    def add_to_memory(
        self,
        entry_type: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> MemoryEntry:
        """Add entry to memory"""
        entry = MemoryEntry(
            id=self._generate_id(content),
            entry_type=entry_type,
            content=content,
            metadata=metadata or {}
        )
        
        self.short_term.append(entry)
        
        # Keep short-term memory bounded
        if len(self.short_term) > 100:
            self.short_term = self.short_term[-100:]
        
        # Add to vector database if available
        if self.collection:
            try:
                self.collection.add(
                    documents=[content],
                    metadatas=[{
                        "type": entry_type,
                        "timestamp": entry.timestamp.isoformat(),
                        **{k: str(v) for k, v in (metadata or {}).items()}
                    }],
                    ids=[entry.id]
                )
            except Exception as e:
                print(f"ChromaDB add failed: {e}")
        
        return entry
    
    def search_memory(
        self,
        query: str,
        n_results: int = 5,
        entry_type: str = None
    ) -> List[MemoryEntry]:
        """Search memory semantically"""
        if self.collection:
            try:
                where_filter = {"type": entry_type} if entry_type else None
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_filter
                )
                
                entries = []
                for i, doc in enumerate(results['documents'][0]):
                    meta = results['metadatas'][0][i] if results['metadatas'] else {}
                    entry = MemoryEntry(
                        id=results['ids'][0][i],
                        entry_type=meta.get('type', 'unknown'),
                        content=doc,
                        metadata=meta
                    )
                    entries.append(entry)
                return entries
            except Exception as e:
                print(f"ChromaDB search failed: {e}")
        
        # Fallback: simple text matching
        query_lower = query.lower()
        matches = [
            e for e in self.short_term
            if query_lower in e.content.lower()
        ]
        return matches[:n_results]
    
    def get_recent_context(
        self,
        n: int = 10,
        entry_type: str = None
    ) -> List[MemoryEntry]:
        """Get recent memory entries"""
        if entry_type:
            filtered = [e for e in self.short_term if e.entry_type == entry_type]
        else:
            filtered = self.short_term
        
        return filtered[-n:]
    
    def add_pattern(
        self,
        name: str,
        services: List[str],
        techniques: List[str],
        success_rate: float,
        notes: str = ""
    ) -> AttackPattern:
        """Add attack pattern"""
        pattern = AttackPattern(
            pattern_id=self._generate_id(name),
            name=name,
            services=services,
            techniques=techniques,
            success_rate=success_rate,
            last_used=datetime.now(),
            notes=notes
        )
        
        self.patterns[pattern.pattern_id] = pattern
        self._save_patterns()
        return pattern
    
    def find_patterns(
        self,
        services: List[str] = None,
        min_success_rate: float = 0.0
    ) -> List[AttackPattern]:
        """Find matching attack patterns"""
        matches = []
        
        for pattern in self.patterns.values():
            if min_success_rate and pattern.success_rate < min_success_rate:
                continue
            
            if services:
                service_match = any(
                    s.lower() in [ps.lower() for ps in pattern.services]
                    for s in services
                )
                if not service_match:
                    continue
            
            matches.append(pattern)
        
        # Sort by success rate
        return sorted(matches, key=lambda p: p.success_rate, reverse=True)
    
    def add_fingerprint(
        self,
        target: str,
        fingerprint: Dict[str, Any]
    ):
        """Add/update target fingerprint"""
        self.target_fingerprints[target] = {
            **fingerprint,
            "last_seen": datetime.now().isoformat()
        }
        self._save_fingerprints()
    
    def get_fingerprint(self, target: str) -> Optional[Dict]:
        """Get target fingerprint"""
        return self.target_fingerprints.get(target)
    
    def export_session(self, session_id: str) -> str:
        """Export session to file"""
        session_file = self.data_dir / f"session_{session_id}.json"
        
        data = {
            "session_id": session_id,
            "exported": datetime.now().isoformat(),
            "memory": [
                {
                    "id": e.id,
                    "type": e.entry_type,
                    "content": e.content,
                    "metadata": e.metadata,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in self.short_term
            ]
        }
        
        with open(session_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return str(session_file)
    
    def import_session(self, session_file: str):
        """Import session from file"""
        with open(session_file) as f:
            data = json.load(f)
        
        for entry_data in data.get("memory", []):
            entry = MemoryEntry(
                id=entry_data["id"],
                entry_type=entry_data["type"],
                content=entry_data["content"],
                metadata=entry_data["metadata"],
                timestamp=datetime.fromisoformat(entry_data["timestamp"])
            )
            self.short_term.append(entry)
    
    def clear_session(self):
        """Clear current session memory"""
        self.short_term = []


# Singleton instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(data_dir: str = None) -> MemoryManager:
    """Get or create memory manager instance"""
    global _memory_manager
    
    if _memory_manager is None:
        data_dir = data_dir or os.getenv("WORKSPACE_PATH", "./data")
        _memory_manager = MemoryManager(data_dir)
    
    return _memory_manager
