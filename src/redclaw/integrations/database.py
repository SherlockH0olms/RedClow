"""
RedClaw - Database Integration
PostgreSQL, Redis, Neo4j connections
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import os
import json


@dataclass
class Session:
    """Pentest session"""
    session_id: str
    target: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    findings_count: int = 0
    metadata: Dict = None


@dataclass
class Finding:
    """Security finding for database"""
    finding_id: str
    session_id: str
    severity: str
    title: str
    description: str
    evidence: str
    remediation: str
    created_at: datetime


class DatabaseManager:
    """
    Database Manager
    
    Handles persistence to:
    - PostgreSQL (sessions, findings, reports)
    - Redis (cache, real-time state)
    - Neo4j (attack graphs, relationships)
    
    Falls back to SQLite/JSON if not configured
    """
    
    def __init__(self):
        self.postgres_url = os.getenv("DATABASE_URL")
        self.redis_url = os.getenv("REDIS_URL")
        self.neo4j_url = os.getenv("NEO4J_URL")
        
        self._postgres_conn = None
        self._redis_conn = None
        self._neo4j_driver = None
        
        self._use_fallback = False
        self._fallback_storage: Dict[str, List] = {
            "sessions": [],
            "findings": []
        }
    
    async def connect(self) -> bool:
        """Connect to databases"""
        connected = False
        
        # Try PostgreSQL
        if self.postgres_url:
            try:
                import asyncpg
                self._postgres_conn = await asyncpg.connect(self.postgres_url)
                await self._init_postgres_tables()
                connected = True
            except Exception as e:
                print(f"PostgreSQL connection failed: {e}")
        
        # Try Redis
        if self.redis_url:
            try:
                import redis.asyncio as redis
                self._redis_conn = redis.from_url(self.redis_url)
                await self._redis_conn.ping()
            except Exception as e:
                print(f"Redis connection failed: {e}")
        
        # Try Neo4j
        if self.neo4j_url:
            try:
                from neo4j import AsyncGraphDatabase
                neo4j_auth = (
                    os.getenv("NEO4J_USER", "neo4j"),
                    os.getenv("NEO4J_PASSWORD", "")
                )
                self._neo4j_driver = AsyncGraphDatabase.driver(
                    self.neo4j_url,
                    auth=neo4j_auth
                )
            except Exception as e:
                print(f"Neo4j connection failed: {e}")
        
        if not connected:
            self._use_fallback = True
            print("Using fallback JSON storage")
            self._load_fallback()
        
        return connected or self._use_fallback
    
    async def _init_postgres_tables(self):
        """Initialize PostgreSQL tables"""
        await self._postgres_conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR(50) PRIMARY KEY,
                target VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                findings_count INTEGER DEFAULT 0,
                metadata JSONB
            );
            
            CREATE TABLE IF NOT EXISTS findings (
                finding_id VARCHAR(50) PRIMARY KEY,
                session_id VARCHAR(50) REFERENCES sessions(session_id),
                severity VARCHAR(20) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                evidence TEXT,
                remediation TEXT,
                created_at TIMESTAMP NOT NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_findings_session ON findings(session_id);
            CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);
        """)
    
    def _load_fallback(self):
        """Load fallback JSON storage"""
        storage_file = "./data/storage.json"
        if os.path.exists(storage_file):
            with open(storage_file) as f:
                self._fallback_storage = json.load(f)
    
    def _save_fallback(self):
        """Save fallback storage"""
        os.makedirs("./data", exist_ok=True)
        with open("./data/storage.json", 'w') as f:
            json.dump(self._fallback_storage, f, indent=2, default=str)
    
    async def create_session(self, target: str, metadata: Dict = None) -> Session:
        """Create new session"""
        session = Session(
            session_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            target=target,
            status="active",
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        
        if self._postgres_conn:
            await self._postgres_conn.execute("""
                INSERT INTO sessions (session_id, target, status, start_time, metadata)
                VALUES ($1, $2, $3, $4, $5)
            """, session.session_id, session.target, session.status,
                session.start_time, json.dumps(session.metadata))
        else:
            self._fallback_storage["sessions"].append({
                "session_id": session.session_id,
                "target": session.target,
                "status": session.status,
                "start_time": session.start_time.isoformat(),
                "metadata": session.metadata
            })
            self._save_fallback()
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        if self._postgres_conn:
            row = await self._postgres_conn.fetchrow("""
                SELECT * FROM sessions WHERE session_id = $1
            """, session_id)
            
            if row:
                return Session(
                    session_id=row["session_id"],
                    target=row["target"],
                    status=row["status"],
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    findings_count=row["findings_count"],
                    metadata=row["metadata"]
                )
        else:
            for s in self._fallback_storage["sessions"]:
                if s["session_id"] == session_id:
                    return Session(
                        session_id=s["session_id"],
                        target=s["target"],
                        status=s["status"],
                        start_time=datetime.fromisoformat(s["start_time"]),
                        metadata=s.get("metadata", {})
                    )
        
        return None
    
    async def update_session(self, session_id: str, **kwargs):
        """Update session"""
        if self._postgres_conn:
            sets = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys()))
            values = [session_id] + list(kwargs.values())
            
            await self._postgres_conn.execute(f"""
                UPDATE sessions SET {sets} WHERE session_id = $1
            """, *values)
        else:
            for s in self._fallback_storage["sessions"]:
                if s["session_id"] == session_id:
                    s.update(kwargs)
            self._save_fallback()
    
    async def add_finding(self, finding: Finding):
        """Add finding to database"""
        if self._postgres_conn:
            await self._postgres_conn.execute("""
                INSERT INTO findings 
                (finding_id, session_id, severity, title, description, evidence, remediation, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, finding.finding_id, finding.session_id, finding.severity,
                finding.title, finding.description, finding.evidence,
                finding.remediation, finding.created_at)
            
            # Update session findings count
            await self._postgres_conn.execute("""
                UPDATE sessions SET findings_count = findings_count + 1 
                WHERE session_id = $1
            """, finding.session_id)
        else:
            self._fallback_storage["findings"].append({
                "finding_id": finding.finding_id,
                "session_id": finding.session_id,
                "severity": finding.severity,
                "title": finding.title,
                "description": finding.description,
                "evidence": finding.evidence,
                "remediation": finding.remediation,
                "created_at": finding.created_at.isoformat()
            })
            self._save_fallback()
    
    async def get_findings(
        self,
        session_id: str = None,
        severity: str = None
    ) -> List[Finding]:
        """Get findings with optional filters"""
        if self._postgres_conn:
            query = "SELECT * FROM findings WHERE 1=1"
            params = []
            
            if session_id:
                params.append(session_id)
                query += f" AND session_id = ${len(params)}"
            
            if severity:
                params.append(severity)
                query += f" AND severity = ${len(params)}"
            
            rows = await self._postgres_conn.fetch(query, *params)
            
            return [
                Finding(
                    finding_id=r["finding_id"],
                    session_id=r["session_id"],
                    severity=r["severity"],
                    title=r["title"],
                    description=r["description"],
                    evidence=r["evidence"],
                    remediation=r["remediation"],
                    created_at=r["created_at"]
                )
                for r in rows
            ]
        else:
            findings = self._fallback_storage["findings"]
            
            if session_id:
                findings = [f for f in findings if f["session_id"] == session_id]
            if severity:
                findings = [f for f in findings if f["severity"] == severity]
            
            return [
                Finding(
                    finding_id=f["finding_id"],
                    session_id=f["session_id"],
                    severity=f["severity"],
                    title=f["title"],
                    description=f["description"],
                    evidence=f["evidence"],
                    remediation=f["remediation"],
                    created_at=datetime.fromisoformat(f["created_at"])
                )
                for f in findings
            ]
    
    # Redis cache methods
    async def cache_set(self, key: str, value: Any, ttl: int = 3600):
        """Set cache value"""
        if self._redis_conn:
            await self._redis_conn.setex(key, ttl, json.dumps(value))
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        if self._redis_conn:
            value = await self._redis_conn.get(key)
            if value:
                return json.loads(value)
        return None
    
    # Neo4j graph methods
    async def add_attack_node(
        self,
        node_type: str,
        properties: Dict
    ):
        """Add node to attack graph"""
        if self._neo4j_driver:
            async with self._neo4j_driver.session() as session:
                await session.run(
                    f"CREATE (n:{node_type} $props)",
                    props=properties
                )
    
    async def add_attack_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Dict = None
    ):
        """Add relationship to attack graph"""
        if self._neo4j_driver:
            async with self._neo4j_driver.session() as session:
                await session.run("""
                    MATCH (a {id: $from_id}), (b {id: $to_id})
                    CREATE (a)-[r:$rel_type $props]->(b)
                """, from_id=from_id, to_id=to_id, rel_type=rel_type,
                    props=properties or {})
    
    async def close(self):
        """Close connections"""
        if self._postgres_conn:
            await self._postgres_conn.close()
        if self._redis_conn:
            await self._redis_conn.close()
        if self._neo4j_driver:
            await self._neo4j_driver.close()


# Singleton
_db_manager: Optional[DatabaseManager] = None


async def get_database() -> DatabaseManager:
    """Get database manager"""
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.connect()
    
    return _db_manager
