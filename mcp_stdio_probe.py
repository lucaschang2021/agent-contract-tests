"""Minimal MCP JSON-RPC stdio probe for a trusted local test server.

Supports initialize, notifications/initialized, tools/list and tools/call.
This is a test probe, not a complete MCP client or security sandbox.
"""
import json
import queue
import threading
import subprocess
import time


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
        self.poisoned = False

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
        if self.poisoned:
            raise MCPProtocolError('session unusable after previous protocol failure')
        self.next_id += 1
        request_id = self.next_id
        self._send({'jsonrpc': '2.0', 'id': request_id,
                    'method': method, 'params': params or {}})
        deadline = time.monotonic() + self.timeout
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise MCPProtocolError('response timeout')
                try:
                    line = self.lines.get(timeout=remaining)
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
                if not isinstance(message, dict) or message.get('jsonrpc') != '2.0':
                    raise MCPProtocolError('invalid JSON-RPC message')
                if 'id' not in message and isinstance(message.get('method'), str):
                    self.events.append({'event': 'notification', 'method': message['method']})
                    continue
                if message.get('id') != request_id:
                    raise MCPProtocolError('unexpected response ID')
                if 'error' in message:
                    raise MCPProtocolError('server returned JSON-RPC error')
                if 'result' not in message:
                    raise MCPProtocolError('response missing result')
                self.events.append({'event': 'response', 'method': method})
                return message['result']
        except MCPProtocolError:
            self.poisoned = True
            raise

    def initialize(self):
        result = self.request('initialize', {'protocolVersion': '2025-06-18',
                    'capabilities': {}, 'clientInfo': {'name': 'agent-contract-tests', 'version': '0.4'}})
        self._send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        return result

    def list_tools(self):
        return self.request('tools/list')

    def call_tool(self, name, arguments=None):
        return self.request('tools/call', {'name': name, 'arguments': arguments or {}})
