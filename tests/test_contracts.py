import unittest
from agent_contracts import ToolRunner, ToolStatus, ToolUnavailable, RecoveryState, verify_artifact_manifest

class CapabilityTests(unittest.TestCase):
    def test_missing_tool_fails_fast_without_invocation_or_retry(self):
        runner = ToolRunner(ToolStatus.NOT_REGISTERED)
        with self.assertRaises(ToolUnavailable) as ctx:
            runner.invoke()
        self.assertEqual(ctx.exception.status, ToolStatus.NOT_REGISTERED)
        self.assertEqual((runner.calls, runner.retries), (0, 0))

    def test_distinct_failure_categories(self):
        for status in (ToolStatus.DISCONNECTED, ToolStatus.AUTH_EXPIRED, ToolStatus.DENIED):
            with self.subTest(status=status):
                runner = ToolRunner(status)
                with self.assertRaises(ToolUnavailable) as ctx:
                    runner.invoke()
                self.assertEqual(ctx.exception.status, status)
                self.assertEqual(runner.calls, 0)

    def test_reconnected_tool_must_be_checked_again(self):
        runner = ToolRunner(ToolStatus.DISCONNECTED)
        with self.assertRaises(ToolUnavailable):
            runner.invoke()
        runner.status = ToolStatus.READY
        self.assertEqual(runner.invoke(), 'ok')
        self.assertEqual(runner.calls, 1)

class RecoveryTests(unittest.TestCase):
    def test_persisted_false_can_be_reconciled(self):
        state = RecoveryState(ownership_confirmed=True, completed=False)
        state.reconcile_verified_coverage(True)
        self.assertTrue(state.completed)
        self.assertFalse(state.pending_intent)

    def test_late_success_is_reused_after_timeout(self):
        state = RecoveryState(ownership_confirmed=False, completed=False)
        self.assertTrue(state.request_stop())
        self.assertEqual(state.stop_requests, 1)
        # Original wait timed out; a late success arrives later.
        state.receive_stop_success()
        self.assertFalse(state.request_stop())
        self.assertEqual(state.stop_requests, 1)
        self.assertTrue(state.completed)

    def test_artifact_gate_flags_missing_setting(self):
        result = verify_artifact_manifest({'version':'1.0'}, {'version':'1.0', 'longPathAware':True})
        self.assertTrue(result['version'])
        self.assertFalse(result['longPathAware'])

if __name__ == '__main__':
    unittest.main()
