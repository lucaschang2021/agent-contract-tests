"""Minimal MCP JSON-RPC stdio probe for a trusted local test server.

Supports initialize, notifications/initialized, tools/list and tools/call.
This is a test probe, not a complete MCP client or security sandbox.
"""
import json
import queue
import threading
import subprocess


class MCPProtocolError(RuntimeError):
    pass


class MCPStdioProbe:
    def __init__(self, argv, timeout=3):
        self.argv = argv
        self.timeout = timeout
        self.process = None
        self.next_id = 0
        self.lines = queue.Queue()
        self.events = []

    def __enter__(self):
        self.process = subprocess.Popen(self.argv, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                        bufsize=0)
        def read_lines():
            while True:
                line = self.process.stdout.readline()
                self.lines.put(line)
                if not line:
                    return
        threading.Thread(target=read_lines, daemon=True).start()
        return self

    def __exit__(self, *_):
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            for stream in (self.process.stdin, self.process.stdout):
                if stream:
                    stream.close()

    def _send(self, obj):
        payload = (json.dumps(obj, separators=(',', ':')) + '\n').encode('utf-8')
        self.process.stdin.write(payload)
        self.process.stdin.flush()
        self.events.append({'event': 'send', 'method': obj.get('method')})

    def request(self, method, params=None):
        self.next_id += 1
        request_id = self.next_id
        self._send({'jsonrpc': '2.0', 'id': request_id,
                    'method': method, 'params': params or {}})
        try:
            line = self.lines.get(timeout=self.timeout)
        except queue.Empty as exc:
            raise MCPProtocolError('response timeout') from exc
        if not line:
            raise MCPProtocolError('server closed stdout')
        if len(line) > 1024 * 1024:
            raise MCPProtocolError('response line too large')
        try:
            message = json.loads(line.decode('utf-8'))
        except (ValueError, UnicodeDecodeError) as exc:
            raise MCPProtocolError('non-JSON data on protocol stdout') from exc
        if message.get('id') != request_id:
            raise MCPProtocolError('unexpected response ID')
        if message.get('jsonrpc') != '2.0':
            raise MCPProtocolError('invalid JSON-RPC version')
        if 'error' in message:
            raise MCPProtocolError('server returned JSON-RPC error')
        self.events.append({'event': 'response', 'method': method})
        return message.get('result')

    def initialize(self):
        result = self.request('initialize', {'protocolVersion': '2025-06-18',
                    'capabilities': {}, 'clientInfo': {'name': 'agent-contract-tests', 'version': '0.4'}})
        self._send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        return result

    def list_tools(self):
        return self.request('tools/list')

    def call_tool(self, name, arguments=None):
        return self.request('tools/call', {'name': name, 'arguments': arguments or {}})
