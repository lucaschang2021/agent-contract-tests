"""Local instrumented tool registry: observable real Python dispatch, no external services."""
from dataclasses import dataclass, field
from typing import Callable, Dict
import json
import time
from agent_contracts import ToolStatus, ToolUnavailable

@dataclass
class LocalAgentRuntime:
    registry: Dict[str, Callable] = field(default_factory=dict)
    states: Dict[str, ToolStatus] = field(default_factory=dict)
    events: list = field(default_factory=list)
    attempts: int = 0

    def record(self, event: str, tool: str, **details):
        self.events.append({'monotonic_ns': time.monotonic_ns(), 'event': event,
                            'tool': tool, **details})

    def register(self, name: str, handler: Callable, status=ToolStatus.READY):
        self.registry[name] = handler
        self.states[name] = status
        self.record('registered', name, status=status.value)

    def set_status(self, name: str, status: ToolStatus):
        self.states[name] = status
        self.record('status_changed', name, status=status.value)

    def invoke(self, name: str, *args, **kwargs):
        # The effective registry, not a cached permission flag, is authoritative.
        status = (ToolStatus.NOT_REGISTERED if name not in self.registry
                  else self.states.get(name, ToolStatus.NOT_REGISTERED))
        self.record('capability_checked', name, status=status.value)
        if status != ToolStatus.READY:
            self.record('terminal_unavailable', name, status=status.value)
            raise ToolUnavailable(status)
        self.attempts += 1
        self.record('invocation_started', name)
        try:
            result = self.registry[name](*args, **kwargs)
        except Exception as exc:
            self.record('invocation_failed', name, error_type=type(exc).__name__)
            raise
        self.record('invocation_succeeded', name)
        return result

    def export_jsonl(self):
        return '\n'.join(json.dumps(e, ensure_ascii=False) for e in self.events) + '\n'
