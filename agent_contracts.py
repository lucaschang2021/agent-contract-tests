"""Reference contracts for agent capability and recovery; not Codex internals."""
from dataclasses import dataclass
from enum import Enum

class ToolStatus(str, Enum):
    READY = 'ready'
    NOT_REGISTERED = 'not_registered'
    DISCONNECTED = 'disconnected'
    AUTH_EXPIRED = 'auth_expired'
    DENIED = 'denied'

class ToolUnavailable(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__(f'tool unavailable: {status.value}')

@dataclass
class ToolRunner:
    status: ToolStatus
    calls: int = 0
    retries: int = 0
    def invoke(self):
        if self.status != ToolStatus.READY:
            raise ToolUnavailable(self.status)
        self.calls += 1
        return 'ok'

@dataclass
class RecoveryState:
    ownership_confirmed: bool = False
    completed: bool = False
    pending_intent: bool = True
    stop_requests: int = 0
    late_success: bool = False

    def request_stop(self):
        if self.completed or self.late_success:
            self.completed = True
            self.pending_intent = False
            return False
        self.stop_requests += 1
        return True

    def receive_stop_success(self):
        self.late_success = True
        self.ownership_confirmed = True
        self.completed = True
        self.pending_intent = False

    def reconcile_verified_coverage(self, verified: bool):
        if verified:
            self.completed = True
            self.pending_intent = False


def verify_artifact_manifest(manifest: dict, required: dict):
    """Illustrative metadata gate, not binary inspection."""
    return {k: (manifest.get(k) == v) for k, v in required.items()}
