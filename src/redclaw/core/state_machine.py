"""
RedClaw Core - State Machine
PTES-based workflow state management
"""

from enum import Enum
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from datetime import datetime


class Phase(Enum):
    """Penetration Testing Execution Standard phases"""
    PRE_ENGAGEMENT = "pre_engagement"
    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"
    ENUMERATION = "enumeration"
    VULNERABILITY_ANALYSIS = "vulnerability_analysis"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    REPORTING = "reporting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ActionResult:
    """Result of an action"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    next_phase: Optional[Phase] = None
    artifacts: List[str] = field(default_factory=list)


@dataclass
class StateTransition:
    """State transition record"""
    from_phase: Phase
    to_phase: Phase
    trigger: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict = field(default_factory=dict)


class StateMachine:
    """
    PTES State Machine
    
    Manages workflow state transitions with:
    - Valid transition enforcement
    - Error handling and recovery
    - State history tracking
    - Callback hooks
    """
    
    # Valid state transitions
    TRANSITIONS = {
        Phase.PRE_ENGAGEMENT: [Phase.RECONNAISSANCE, Phase.ERROR],
        Phase.RECONNAISSANCE: [Phase.SCANNING, Phase.ERROR, Phase.REPORTING],
        Phase.SCANNING: [Phase.ENUMERATION, Phase.VULNERABILITY_ANALYSIS, Phase.ERROR, Phase.REPORTING],
        Phase.ENUMERATION: [Phase.VULNERABILITY_ANALYSIS, Phase.SCANNING, Phase.ERROR, Phase.REPORTING],
        Phase.VULNERABILITY_ANALYSIS: [Phase.EXPLOITATION, Phase.ENUMERATION, Phase.ERROR, Phase.REPORTING],
        Phase.EXPLOITATION: [Phase.POST_EXPLOITATION, Phase.VULNERABILITY_ANALYSIS, Phase.ERROR, Phase.REPORTING],
        Phase.POST_EXPLOITATION: [Phase.REPORTING, Phase.EXPLOITATION, Phase.ERROR],
        Phase.REPORTING: [Phase.COMPLETED],
        Phase.COMPLETED: [],
        Phase.ERROR: [Phase.PRE_ENGAGEMENT, Phase.RECONNAISSANCE]  # Recovery options
    }
    
    def __init__(self, initial_phase: Phase = Phase.PRE_ENGAGEMENT):
        self.current_phase = initial_phase
        self.history: List[StateTransition] = []
        self.callbacks: Dict[str, List[Callable]] = {
            "on_enter": [],
            "on_exit": [],
            "on_error": []
        }
        self.error_count = 0
        self.max_retries = 3
    
    def can_transition(self, to_phase: Phase) -> bool:
        """Check if transition is valid"""
        return to_phase in self.TRANSITIONS.get(self.current_phase, [])
    
    def transition(self, to_phase: Phase, trigger: str = "auto", data: Dict = None) -> bool:
        """
        Transition to new phase
        
        Args:
            to_phase: Target phase
            trigger: What triggered this transition
            data: Optional context data
            
        Returns:
            True if transition successful
        """
        if not self.can_transition(to_phase):
            return False
        
        # Exit callbacks
        for callback in self.callbacks["on_exit"]:
            try:
                callback(self.current_phase, to_phase, data)
            except:
                pass
        
        # Record transition
        transition = StateTransition(
            from_phase=self.current_phase,
            to_phase=to_phase,
            trigger=trigger,
            data=data or {}
        )
        self.history.append(transition)
        
        # Update state
        old_phase = self.current_phase
        self.current_phase = to_phase
        
        # Reset error count on successful non-error transition
        if to_phase != Phase.ERROR:
            self.error_count = 0
        
        # Enter callbacks
        for callback in self.callbacks["on_enter"]:
            try:
                callback(old_phase, to_phase, data)
            except:
                pass
        
        return True
    
    def handle_error(self, error: str, recoverable: bool = True) -> bool:
        """
        Handle error with optional recovery
        
        Args:
            error: Error message
            recoverable: Whether to attempt recovery
            
        Returns:
            True if recovered, False otherwise
        """
        self.error_count += 1
        
        # Error callbacks
        for callback in self.callbacks["on_error"]:
            try:
                callback(self.current_phase, error, self.error_count)
            except:
                pass
        
        if not recoverable or self.error_count >= self.max_retries:
            self.transition(Phase.ERROR, "error", {"error": error, "count": self.error_count})
            return False
        
        # Stay in current phase for retry
        return True
    
    def recover(self, to_phase: Phase = Phase.RECONNAISSANCE) -> bool:
        """Recover from error state"""
        if self.current_phase != Phase.ERROR:
            return True
        
        if self.can_transition(to_phase):
            self.error_count = 0
            return self.transition(to_phase, "recovery")
        
        return False
    
    def on_enter(self, callback: Callable):
        """Register on-enter callback"""
        self.callbacks["on_enter"].append(callback)
    
    def on_exit(self, callback: Callable):
        """Register on-exit callback"""
        self.callbacks["on_exit"].append(callback)
    
    def on_error(self, callback: Callable):
        """Register on-error callback"""
        self.callbacks["on_error"].append(callback)
    
    def get_valid_transitions(self) -> List[Phase]:
        """Get list of valid next phases"""
        return self.TRANSITIONS.get(self.current_phase, [])
    
    def get_history(self) -> List[Dict]:
        """Get transition history as dicts"""
        return [
            {
                "from": t.from_phase.value,
                "to": t.to_phase.value,
                "trigger": t.trigger,
                "timestamp": t.timestamp.isoformat(),
                "data": t.data
            }
            for t in self.history
        ]
    
    def reset(self, to_phase: Phase = Phase.PRE_ENGAGEMENT):
        """Reset state machine"""
        self.current_phase = to_phase
        self.history = []
        self.error_count = 0
    
    @property
    def is_complete(self) -> bool:
        """Check if workflow is complete"""
        return self.current_phase == Phase.COMPLETED
    
    @property
    def is_error(self) -> bool:
        """Check if in error state"""
        return self.current_phase == Phase.ERROR
    
    @property
    def progress(self) -> float:
        """Get progress percentage (0-100)"""
        phases = list(Phase)
        if self.current_phase == Phase.COMPLETED:
            return 100.0
        if self.current_phase == Phase.ERROR:
            return -1.0
        
        try:
            idx = phases.index(self.current_phase)
            # Exclude ERROR and COMPLETED from count
            total = len(phases) - 2
            return (idx / total) * 100
        except:
            return 0.0


class WorkflowContext:
    """Context passed through workflow"""
    
    def __init__(self, target: str, scope: List[str] = None):
        self.target = target
        self.scope = scope or []
        self.findings: List[Dict] = []
        self.artifacts: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None
    
    def add_finding(self, finding: Dict):
        """Add security finding"""
        finding["timestamp"] = datetime.now().isoformat()
        self.findings.append(finding)
    
    def add_artifact(self, path: str):
        """Add artifact path"""
        self.artifacts.append(path)
    
    def set_metadata(self, key: str, value: Any):
        """Set metadata value"""
        self.metadata[key] = value
    
    def complete(self):
        """Mark workflow as complete"""
        self.completed_at = datetime.now()
    
    @property
    def duration(self) -> float:
        """Get duration in seconds"""
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds()
    
    def to_dict(self) -> Dict:
        """Export as dictionary"""
        return {
            "target": self.target,
            "scope": self.scope,
            "findings": self.findings,
            "artifacts": self.artifacts,
            "metadata": self.metadata,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration
        }
