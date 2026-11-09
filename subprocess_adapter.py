"""Subprocess-backed tool adapter for observable local execution.

No vendor runtime integration, external network, or model API usage.
"""
import subprocess
from instrumented_runtime import LocalAgentRuntime
from agent_contracts import ToolStatus


def register_subprocess(runtime: LocalAgentRuntime, name: str, argv, timeout=5):
    """Register a fixed argument vector; never execute through a shell."""
    if not argv or not all(isinstance(arg, str) for arg in argv):
        raise ValueError("argv must be a non-empty list of strings")

    def handler():
        result = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout,
            check=False, shell=False
        )
        if result.returncode:
            raise subprocess.CalledProcessError(
                result.returncode, argv, output=result.stdout, stderr=result.stderr
            )
        return result.stdout

    runtime.register(name, handler, ToolStatus.READY)
