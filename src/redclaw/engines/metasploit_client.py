"""
RedClaw Engines - Metasploit RPC Client
Metasploit Framework Integration via MSFRPC
"""

import asyncio
import msgpack
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MsfSession:
    """Metasploit session"""
    session_id: int
    session_type: str
    tunnel_local: str
    tunnel_peer: str
    via_exploit: str
    via_payload: str
    platform: str
    info: str


@dataclass
class MsfJob:
    """Metasploit job"""
    job_id: int
    name: str
    start_time: datetime


@dataclass
class ExploitResult:
    """Exploit execution result"""
    success: bool
    session_id: Optional[int]
    message: str
    output: str


class MetasploitClient:
    """
    Metasploit RPC Client
    
    Integration with Metasploit Framework via MSFRPC for:
    - Exploit execution
    - Session management
    - Payload generation
    - Post-exploitation
    
    Reference: https://docs.metasploit.com/docs/using-metasploit/basics/using-metasploit.html
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 55553,
        username: str = "msf",
        password: str = "msf",
        ssl: bool = False
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        protocol = "https" if ssl else "http"
        self.url = f"{protocol}://{host}:{port}/api/"
        
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def _call(
        self,
        method: str,
        *args
    ) -> Any:
        """Make RPC call"""
        
        if method != "auth.login" and not self.token:
            raise Exception("Not authenticated. Call login() first.")
        
        params = [method]
        if self.token and method != "auth.login":
            params.append(self.token)
        params.extend(args)
        
        try:
            data = msgpack.packb(params)
            response = await self.client.post(
                self.url,
                content=data,
                headers={"Content-Type": "binary/message-pack"}
            )
            
            if response.status_code == 200:
                return msgpack.unpackb(response.content, raw=False)
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    # ============ Authentication ============
    
    async def login(self) -> bool:
        """Authenticate to MSFRPC"""
        result = await self._call("auth.login", self.username, self.password)
        
        if result.get("result") == "success":
            self.token = result.get("token")
            return True
        return False
    
    async def logout(self) -> bool:
        """Logout from MSFRPC"""
        if self.token:
            result = await self._call("auth.logout", self.token)
            self.token = None
            return result.get("result") == "success"
        return True
    
    # ============ Core ============
    
    async def version(self) -> Dict:
        """Get Metasploit version"""
        return await self._call("core.version")
    
    async def health_check(self) -> bool:
        """Check if MSFRPC is available"""
        try:
            if not self.token:
                success = await self.login()
                if not success:
                    return False
            
            result = await self.version()
            return "version" in result
        except:
            return False
    
    # ============ Modules ============
    
    async def list_exploits(
        self,
        search: str = None
    ) -> List[str]:
        """List available exploits"""
        result = await self._call("module.exploits")
        exploits = result.get("modules", [])
        
        if search:
            exploits = [e for e in exploits if search.lower() in e.lower()]
        
        return exploits
    
    async def list_payloads(
        self,
        search: str = None
    ) -> List[str]:
        """List available payloads"""
        result = await self._call("module.payloads")
        payloads = result.get("modules", [])
        
        if search:
            payloads = [p for p in payloads if search.lower() in p.lower()]
        
        return payloads
    
    async def list_auxiliary(
        self,
        search: str = None
    ) -> List[str]:
        """List auxiliary modules"""
        result = await self._call("module.auxiliary")
        modules = result.get("modules", [])
        
        if search:
            modules = [m for m in modules if search.lower() in m.lower()]
        
        return modules
    
    async def get_module_info(
        self,
        module_type: str,
        module_name: str
    ) -> Dict:
        """Get module information"""
        return await self._call("module.info", module_type, module_name)
    
    async def get_module_options(
        self,
        module_type: str,
        module_name: str
    ) -> Dict:
        """Get module options"""
        return await self._call("module.options", module_type, module_name)
    
    # ============ Exploit Execution ============
    
    async def execute_exploit(
        self,
        exploit_name: str,
        payload_name: str,
        options: Dict
    ) -> ExploitResult:
        """Execute exploit"""
        try:
            # Execute
            result = await self._call(
                "module.execute",
                "exploit",
                exploit_name,
                {**options, "PAYLOAD": payload_name}
            )
            
            if "error" in result:
                return ExploitResult(
                    success=False,
                    session_id=None,
                    message=result.get("error_message", str(result)),
                    output=""
                )
            
            job_id = result.get("job_id")
            
            # Wait for result
            await asyncio.sleep(2)
            
            # Check for session
            sessions = await self.list_sessions()
            new_session = None
            
            for session in sessions:
                if options.get("RHOSTS", "") in session.tunnel_peer:
                    new_session = session
                    break
            
            if new_session:
                return ExploitResult(
                    success=True,
                    session_id=new_session.session_id,
                    message="Exploit successful, session created",
                    output=f"Session {new_session.session_id} opened"
                )
            else:
                return ExploitResult(
                    success=False,
                    session_id=None,
                    message=f"Exploit executed (job {job_id}), no session created",
                    output=str(result)
                )
                
        except Exception as e:
            return ExploitResult(
                success=False,
                session_id=None,
                message=str(e),
                output=""
            )
    
    async def run_auxiliary(
        self,
        module_name: str,
        options: Dict
    ) -> Dict:
        """Run auxiliary module"""
        return await self._call("module.execute", "auxiliary", module_name, options)
    
    # ============ Sessions ============
    
    async def list_sessions(self) -> List[MsfSession]:
        """List active sessions"""
        result = await self._call("session.list")
        
        sessions = []
        for sid, info in result.items():
            if sid == "error":
                continue
            sessions.append(MsfSession(
                session_id=int(sid),
                session_type=info.get("type", ""),
                tunnel_local=info.get("tunnel_local", ""),
                tunnel_peer=info.get("tunnel_peer", ""),
                via_exploit=info.get("via_exploit", ""),
                via_payload=info.get("via_payload", ""),
                platform=info.get("platform", ""),
                info=info.get("info", "")
            ))
        
        return sessions
    
    async def session_shell(
        self,
        session_id: int,
        command: str
    ) -> str:
        """Execute shell command in session"""
        # Write command
        await self._call("session.shell_write", str(session_id), command + "\n")
        
        # Wait and read
        await asyncio.sleep(1)
        result = await self._call("session.shell_read", str(session_id))
        
        return result.get("data", "")
    
    async def session_meterpreter(
        self,
        session_id: int,
        command: str
    ) -> str:
        """Execute meterpreter command"""
        result = await self._call(
            "session.meterpreter_write",
            str(session_id),
            command
        )
        
        await asyncio.sleep(1)
        output = await self._call("session.meterpreter_read", str(session_id))
        
        return output.get("data", "")
    
    async def kill_session(self, session_id: int) -> bool:
        """Kill session"""
        result = await self._call("session.stop", str(session_id))
        return result.get("result") == "success"
    
    # ============ Jobs ============
    
    async def list_jobs(self) -> List[MsfJob]:
        """List running jobs"""
        result = await self._call("job.list")
        
        jobs = []
        for jid, name in result.items():
            if jid == "error":
                continue
            jobs.append(MsfJob(
                job_id=int(jid),
                name=name,
                start_time=datetime.now()
            ))
        
        return jobs
    
    async def kill_job(self, job_id: int) -> bool:
        """Kill job"""
        result = await self._call("job.stop", str(job_id))
        return result.get("result") == "success"
    
    # ============ Console ============
    
    async def create_console(self) -> Optional[str]:
        """Create console"""
        result = await self._call("console.create")
        return result.get("id")
    
    async def console_write(
        self,
        console_id: str,
        command: str
    ) -> bool:
        """Write to console"""
        result = await self._call("console.write", console_id, command + "\n")
        return result.get("wrote", 0) > 0
    
    async def console_read(self, console_id: str) -> str:
        """Read from console"""
        result = await self._call("console.read", console_id)
        return result.get("data", "")
    
    async def destroy_console(self, console_id: str) -> bool:
        """Destroy console"""
        result = await self._call("console.destroy", console_id)
        return result.get("result") == "success"
    
    # ============ Payloads ============
    
    async def generate_payload(
        self,
        payload_name: str,
        options: Dict,
        format: str = "exe"
    ) -> Optional[bytes]:
        """Generate payload"""
        result = await self._call(
            "module.execute",
            "payload",
            payload_name,
            {**options, "FORMAT": format}
        )
        
        return result.get("payload")
    
    # ============ Search ============
    
    async def search(self, query: str) -> List[Dict]:
        """Search for modules"""
        # Use console for search
        console_id = await self.create_console()
        if not console_id:
            return []
        
        try:
            await self.console_write(console_id, f"search {query}")
            await asyncio.sleep(3)  # Wait for search
            
            output = await self.console_read(console_id)
            
            # Parse results
            results = []
            for line in output.split("\n"):
                if "/" in line and not line.startswith("#"):
                    parts = line.split()
                    if len(parts) >= 2:
                        results.append({
                            "name": parts[0].strip(),
                            "description": " ".join(parts[1:])
                        })
            
            return results
        finally:
            await self.destroy_console(console_id)
    
    async def close(self):
        """Close client"""
        await self.logout()
        await self.client.aclose()
