import os
import sys
import unittest
from mcp_stdio_probe import MCPStdioProbe, MCPProtocolError

FIXTURE = os.path.join(os.path.dirname(__file__), 'fixtures', 'mcp_test_server.py')

class MCPStdioProbeTests(unittest.TestCase):
    def test_initialize_list_and_call_real_process(self):
        with MCPStdioProbe([sys.executable, '-u', FIXTURE]) as probe:
            init = probe.initialize()
            self.assertEqual(init['serverInfo']['name'], 'fixture')
            self.assertEqual(probe.list_tools()['tools'][0]['name'], 'echo')
            result = probe.call_tool('echo', {'text': 'hello'})
            self.assertEqual(result['content'][0]['text'], 'hello')
            self.assertEqual(len([e for e in probe.events if e['event']=='response']), 3)

    def test_non_json_stdout_rejected(self):
        with MCPStdioProbe([sys.executable, '-u', '-c', "print('noise', flush=True); import time; time.sleep(.1)"]) as probe:
            with self.assertRaisesRegex(MCPProtocolError, 'non-JSON'):
                probe.request('initialize')

    def test_timeout_is_bounded(self):
        with MCPStdioProbe([sys.executable, '-u', '-c', 'import time; time.sleep(2)'], timeout=.1) as probe:
            with self.assertRaisesRegex(MCPProtocolError, 'timeout'):
                probe.request('initialize')

if __name__ == '__main__':
    unittest.main()
