import subprocess
import sys
import unittest
from agent_contracts import ToolStatus, ToolUnavailable
from instrumented_runtime import LocalAgentRuntime
from subprocess_adapter import register_subprocess


class SubprocessAdapterTests(unittest.TestCase):
    def test_real_local_subprocess_execution(self):
        runtime = LocalAgentRuntime()
        register_subprocess(runtime, 'python', [sys.executable, '-c', "print('ok')"])
        self.assertEqual(runtime.invoke('python').strip(), 'ok')
        self.assertEqual(runtime.attempts, 1)
        self.assertEqual(runtime.events[-1]['event'], 'invocation_succeeded')

    def test_revoked_tool_never_launches_subprocess(self):
        runtime = LocalAgentRuntime()
        register_subprocess(runtime, 'python', [sys.executable, '-c', "print('ok')"])
        runtime.set_status('python', ToolStatus.DENIED)
        with self.assertRaises(ToolUnavailable):
            runtime.invoke('python')
        self.assertEqual(runtime.attempts, 0)

    def test_nonzero_exit_is_observed_as_execution_failure(self):
        runtime = LocalAgentRuntime()
        register_subprocess(runtime, 'python', [sys.executable, '-c', 'import sys; sys.exit(3)'])
        with self.assertRaises(subprocess.CalledProcessError) as ctx:
            runtime.invoke('python')
        self.assertEqual(ctx.exception.returncode, 3)
        self.assertEqual(runtime.events[-1]['event'], 'invocation_failed')


if __name__ == '__main__':
    unittest.main()
