"""
RedClaw - State Machine Controller
Phase tracking, error handling, retry logic
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json


class Phase(Enum):
    """Penetration testing phases"""
    INIT = "init"
    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"
    ENUMERATION = "enumeration"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    LATERAL_MOVEMENT = "lateral_movement"
    DATA_EXFILTRATION = "data_exfiltration"
    CLEANUP = "cleanup"
    REPORTING = "reporting"
    COMPLETE = "complete"
    ERROR = "error"


class ActionResult(Enum):
    """Result of an action"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"


@dataclass
class StateTransition:
    """State transition record"""
    from_phase: Phase
    to_phase: Phase
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ActionRecord:
    """Record of an action taken"""
    action_id: str
    phase: Phase
    action_type: str
    description: str
    result: ActionResult
    output: str
    duration_ms: int
    retry_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class StateMachine:
    """
    State Machine Controller
    
    Features:
    - Phase tracking (PTES methodology)
    - Transition validation
    - Error handling & recovery
    - Retry logic with exponential backoff
    - State persistence
    """
    
    # Valid phase transitions
    VALID_TRANSITIONS = {
        Phase.INIT: [Phase.RECONNAISSANCE, Phase.ERROR],
        Phase.RECONNAISSANCE: [Phase.SCANNING, Phase.ERROR],
        Phase.SCANNING: [Phase.ENUMERATION, Phase.EXPLOITATION, Phase.ERROR],
        Phase.ENUMERATION: [Phase.EXPLOITATION, Phase.ERROR],
        Phase.EXPLOITATION: [Phase.POST_EXPLOITATION, Phase.SCANNING, Phase.ERROR],
        Phase.POST_EXPLOITATION: [Phase.LATERAL_MOVEMENT, Phase.DATA_EXFILTRATION, Phase.CLEANUP, Phase.ERROR],
        Phase.LATERAL_MOVEMENT: [Phase.EXPLOITATION, Phase.POST_EXPLOITATION, Phase.CLEANUP, Phase.ERROR],
        Phase.DATA_EXFILTRATION: [Phase.CLEANUP, Phase.ERROR],
        Phase.CLEANUP: [Phase.REPORTING, Phase.ERROR],
        Phase.REPORTING: [Phase.COMPLETE, Phase.ERROR],
        Phase.ERROR: [Phase.RECONNAISSANCE, Phase.SCANNING, Phase.CLEANUP, Phase.COMPLETE],
    }
    
    # Max retries per phase
    MAX_RETRIES = 3
    
    # Backoff settings (ms)
    BASE_BACKOFF_MS = 1000
    MAX_BACKOFF_MS = 30000
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_phase = Phase.INIT
        self.previous_phase: Optional[Phase] = None
        self.transitions: List[StateTransition] = []
        self.actions: List[ActionRecord] = []
        self.phase_retries: Dict[Phase, int] = {}
        self.callbacks: List[Callable] = []
        self.paused = False
        self.error_message: Optional[str] = None
    
    def add_callback(self, callback: Callable):
        """Add state change callback"""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self, event: str, data: Dict = None):
        """Notify all callbacks"""
        for cb in self.callbacks:
            try:
                cb(event, data or {})
            except Exception as e:
                print(f"Callback error: {e}")
    
    def can_transition(self, to_phase: Phase) -> bool:
        """Check if transition is valid"""
        if self.current_phase == Phase.COMPLETE:
            return False
        
        valid_next = self.VALID_TRANSITIONS.get(self.current_phase, [])
        return to_phase in valid_next
    
    def transition(self, to_phase: Phase, reason: str = "") -> bool:
        """Transition to new phase"""
        if not self.can_transition(to_phase):
            self._notify_callbacks("invalid_transition", {
                "from": self.current_phase.value,
                "to": to_phase.value
            })
            return False
        
        # Record transition
        transition = StateTransition(
            from_phase=self.current_phase,
            to_phase=to_phase,
            reason=reason
        )
        self.transitions.append(transition)
        
        # Update state
        self.previous_phase = self.current_phase
        self.current_phase = to_phase
        
        # Clear error if moving out of error state
        if to_phase != Phase.ERROR:
            self.error_message = None
        
        # Notify callbacks
        self._notify_callbacks("transition", {
            "from": self.previous_phase.value,
            "to": to_phase.value,
            "reason": reason
        })
        
        return True
    
    def record_action(
        self,
        action_type: str,
        description: str,
        result: ActionResult,
        output: str = "",
        duration_ms: int = 0
    ) -> ActionRecord:
        """Record an action"""
        action = ActionRecord(
            action_id=f"{self.session_id}_{len(self.actions)}",
            phase=self.current_phase,
            action_type=action_type,
            description=description,
            result=result,
            output=output,
            duration_ms=duration_ms
        )
        
        self.actions.append(action)
        
        self._notify_callbacks("action", {
            "type": action_type,
            "result": result.value,
            "phase": self.current_phase.value
        })
        
        return action
    
    def handle_error(self, error_message: str, recoverable: bool = True):
        """Handle error state"""
        self.error_message = error_message
        
        if recoverable:
            # Check retry count
            current_retries = self.phase_retries.get(self.current_phase, 0)
            
            if current_retries < self.MAX_RETRIES:
                self.phase_retries[self.current_phase] = current_retries + 1
                self._notify_callbacks("retry", {
                    "phase": self.current_phase.value,
                    "attempt": current_retries + 1,
                    "max_retries": self.MAX_RETRIES
                })
            else:
                self.transition(Phase.ERROR, f"Max retries exceeded: {error_message}")
        else:
            self.transition(Phase.ERROR, error_message)
    
    async def wait_with_backoff(self, attempt: int):
        """Wait with exponential backoff"""
        backoff_ms = min(
            self.BASE_BACKOFF_MS * (2 ** attempt),
            self.MAX_BACKOFF_MS
        )
        
        self._notify_callbacks("backoff", {
            "duration_ms": backoff_ms,
            "attempt": attempt
        })
        
        await asyncio.sleep(backoff_ms / 1000)
    
    def pause(self):
        """Pause state machine"""
        self.paused = True
        self._notify_callbacks("paused", {})
    
    def resume(self):
        """Resume state machine"""
        self.paused = False
        self._notify_callbacks("resumed", {})
    
    def reset(self):
        """Reset to initial state"""
        self.current_phase = Phase.INIT
        self.previous_phase = None
        self.phase_retries = {}
        self.error_message = None
        self.paused = False
        self._notify_callbacks("reset", {})
    
    def get_phase_actions(self, phase: Phase) -> List[ActionRecord]:
        """Get actions for a specific phase"""
        return [a for a in self.actions if a.phase == phase]
    
    def get_phase_stats(self) -> Dict[str, Dict]:
        """Get statistics per phase"""
        stats = {}
        
        for phase in Phase:
            phase_actions = self.get_phase_actions(phase)
            
            if phase_actions:
                success = len([a for a in phase_actions if a.result == ActionResult.SUCCESS])
                failure = len([a for a in phase_actions if a.result == ActionResult.FAILURE])
                total_duration = sum(a.duration_ms for a in phase_actions)
                
                stats[phase.value] = {
                    "actions": len(phase_actions),
                    "success": success,
                    "failure": failure,
                    "success_rate": success / len(phase_actions) if phase_actions else 0,
                    "total_duration_ms": total_duration,
                    "avg_duration_ms": total_duration / len(phase_actions) if phase_actions else 0
                }
        
        return stats
    
    def get_timeline(self) -> List[Dict]:
        """Get timeline of all transitions and actions"""
        timeline = []
        
        for t in self.transitions:
            timeline.append({
                "type": "transition",
                "time": t.timestamp.isoformat(),
                "from": t.from_phase.value,
                "to": t.to_phase.value,
                "reason": t.reason
            })
        
        for a in self.actions:
            timeline.append({
                "type": "action",
                "time": a.timestamp.isoformat(),
                "phase": a.phase.value,
                "action": a.action_type,
                "result": a.result.value
            })
        
        # Sort by time
        timeline.sort(key=lambda x: x["time"])
        return timeline
    
    def export_state(self) -> Dict:
        """Export current state"""
        return {
            "session_id": self.session_id,
            "current_phase": self.current_phase.value,
            "previous_phase": self.previous_phase.value if self.previous_phase else None,
            "paused": self.paused,
            "error_message": self.error_message,
            "transitions_count": len(self.transitions),
            "actions_count": len(self.actions),
            "phase_retries": {p.value: c for p, c in self.phase_retries.items()},
            "stats": self.get_phase_stats()
        }
    
    def save_state(self, filepath: str):
        """Save state to file"""
        data = {
            "session_id": self.session_id,
            "current_phase": self.current_phase.value,
            "previous_phase": self.previous_phase.value if self.previous_phase else None,
            "transitions": [
                {
                    "from": t.from_phase.value,
                    "to": t.to_phase.value,
                    "reason": t.reason,
                    "timestamp": t.timestamp.isoformat()
                }
                for t in self.transitions
            ],
            "actions": [
                {
                    "action_id": a.action_id,
                    "phase": a.phase.value,
                    "action_type": a.action_type,
                    "description": a.description,
                    "result": a.result.value,
                    "output": a.output[:1000],  # Truncate
                    "duration_ms": a.duration_ms,
                    "retry_count": a.retry_count,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in self.actions
            ],
            "phase_retries": {p.value: c for p, c in self.phase_retries.items()}
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_state(self, filepath: str):
        """Load state from file"""
        with open(filepath) as f:
            data = json.load(f)
        
        self.session_id = data["session_id"]
        self.current_phase = Phase(data["current_phase"])
        self.previous_phase = Phase(data["previous_phase"]) if data["previous_phase"] else None
        
        self.transitions = [
            StateTransition(
                from_phase=Phase(t["from"]),
                to_phase=Phase(t["to"]),
                reason=t["reason"],
                timestamp=datetime.fromisoformat(t["timestamp"])
            )
            for t in data["transitions"]
        ]
        
        self.actions = [
            ActionRecord(
                action_id=a["action_id"],
                phase=Phase(a["phase"]),
                action_type=a["action_type"],
                description=a["description"],
                result=ActionResult(a["result"]),
                output=a["output"],
                duration_ms=a["duration_ms"],
                retry_count=a["retry_count"],
                timestamp=datetime.fromisoformat(a["timestamp"])
            )
            for a in data["actions"]
        ]
        
        self.phase_retries = {
            Phase(k): v for k, v in data.get("phase_retries", {}).items()
        }
