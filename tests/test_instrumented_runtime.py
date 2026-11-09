import json
import unittest
from agent_contracts import ToolStatus, ToolUnavailable
from instrumented_runtime import LocalAgentRuntime

class InstrumentedRuntimeTests(unittest.TestCase):
    def test_missing_registration_has_no_invocations(self):
        runtime = LocalAgentRuntime()
        with self.assertRaises(ToolUnavailable) as ctx:
            runtime.invoke('browser')
        self.assertEqual(ctx.exception.status, ToolStatus.NOT_REGISTERED)
        self.assertEqual(runtime.attempts, 0)
        self.assertEqual([e['event'] for e in runtime.events],
                         ['capability_checked', 'terminal_unavailable'])

    def test_revoke_registration_even_if_status_cache_ready(self):
        runtime = LocalAgentRuntime()
        runtime.register('browser', lambda: 'ok')
        del runtime.registry['browser']
        with self.assertRaises(ToolUnavailable) as ctx:
            runtime.invoke('browser')
        self.assertEqual(ctx.exception.status, ToolStatus.NOT_REGISTERED)
        self.assertEqual(runtime.attempts, 0)

    def test_reconnect_requires_effective_ready_status(self):
        runtime = LocalAgentRuntime()
        runtime.register('browser', lambda: 'done', ToolStatus.DISCONNECTED)
        with self.assertRaises(ToolUnavailable):
            runtime.invoke('browser')
        runtime.set_status('browser', ToolStatus.READY)
        self.assertEqual(runtime.invoke('browser'), 'done')
        self.assertEqual(runtime.attempts, 1)

    def test_handler_failure_is_not_misclassified_as_missing_tool(self):
        runtime = LocalAgentRuntime()
        def broken():
            raise ValueError('local handler error')
        runtime.register('browser', broken)
        with self.assertRaises(ValueError):
            runtime.invoke('browser')
        self.assertEqual(runtime.attempts, 1)
        self.assertEqual(runtime.events[-1]['error_type'], 'ValueError')

    def test_jsonl_events_are_parseable(self):
        runtime = LocalAgentRuntime()
        runtime.register('echo', lambda x: x)
        self.assertEqual(runtime.invoke('echo', 42), 42)
        events = [json.loads(line) for line in runtime.export_jsonl().splitlines()]
        self.assertEqual(events[-1]['event'], 'invocation_succeeded')
        self.assertTrue(all(isinstance(e['monotonic_ns'], int) for e in events))

if __name__ == '__main__':
    unittest.main()
