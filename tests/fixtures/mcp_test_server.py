"""A local deterministic MCP-like fixture, not a production server."""
import json
import sys

for line in sys.stdin:
    try:
        req = json.loads(line)
        method = req.get('method')
        if method == 'notifications/initialized':
            continue
        if method == 'initialize':
            result = {'protocolVersion': '2025-06-18', 'capabilities': {'tools': {}},
                      'serverInfo': {'name': 'fixture', 'version': '0.1'}}
        elif method == 'tools/list':
            result = {'tools': [{'name': 'echo', 'description': 'Echo text',
                     'inputSchema': {'type': 'object', 'properties': {'text': {'type': 'string'}}}}]}
        elif method == 'tools/call':
            result = {'content': [{'type': 'text', 'text': req['params']['arguments'].get('text', '')}]}
        else:
            continue
        sys.stdout.write(json.dumps({'jsonrpc': '2.0', 'id': req['id'], 'result': result}) + '\n')
        sys.stdout.flush()
    except Exception:
        sys.stdout.write('not-json\n')
        sys.stdout.flush()
