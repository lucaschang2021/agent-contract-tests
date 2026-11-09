# Agent Contract Tests

An independent, dependency-free Python reference harness for **agent tool availability, fail-fast behavior, recovery state, and verification contracts**.

Inspired by public discussions in [openai/codex#60193](https://github.com/openai/codex/issues/60193) and [openai/codex#60274](https://github.com/openai/codex/issues/60274).

**Independent project:** This does not import, test, patch, reproduce, or claim to fix Codex. It is not affiliated with or endorsed by OpenAI.

## Run

```bash
python -m unittest discover -s tests -v
```

Python 3.9+; standard library only; no API key, model usage, network call, or external service required.

## Coverage (14 tests)

- Missing tool registration fails immediately, with zero handler invocations.
- Distinct disconnected, expired authentication, and denied states.
- Tool capability re-checked after reconnection and registry revocation.
- Handler exceptions distinguished from tool absence.
- JSONL execution events with monotonic timestamps.
- Synthetic persisted incomplete state reconciled with verified evidence.
- Synthetic late stop success reused rather than requesting another stop.
- Illustrative artifact *metadata* gate detects missing requirements; **not** actual PE binary inspection.

The subprocess adapter (`subprocess_adapter.py`) runs an actual local process with `shell=False` and captures exit status. Its three tests cover execution, permission revocation before execution, and nonzero exit codes. This remains a local subprocess integration, **not** Codex or another vendor runtime.\n\nThe instrumented local dispatcher in `instrumented_runtime.py` is real Python execution but is **not** a vendor Agent Runtime or browser-control reproduction.

## Example

```python
from instrumented_runtime import LocalAgentRuntime

runtime = LocalAgentRuntime()
runtime.register("echo", lambda message: message)
assert runtime.invoke("echo", "hello") == "hello"
print(runtime.export_jsonl())
```

## CI

GitHub Actions runs the local tests on Python 3.9, 3.11, and 3.13 on pushes and pull requests. Passing CI verifies only this reference implementation.

## Roadmap

- Integrate with an independently observable, public Agent Runtime.
- Add privacy-safe real execution traces and an evidence matrix.
- Validate Windows PE manifest invariants using an appropriate binary inspection tool.
- Keep synthetic evidence separate from real-world incident reproduction.

## Contributions and license

Reproducible tests, documentation, and narrowly scoped improvements are welcome. Do not share credentials or private logs. This project is released under the [MIT License](LICENSE).
