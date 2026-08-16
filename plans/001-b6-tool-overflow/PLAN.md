# B6 — Headless run_turn sends all tools (exceeds OpenAI 128 limit)

## Problem
`run_turn` in `luna/luna/agent/runtime.py` (line ~1874) calls
`_build_pydantic_ai_tools` without passing `loaded_groups`. When
`loaded_groups=None`, the `_FilteredToolRegistry` disables grouping and
includes ALL tools (~249 static + MacRunner + MCP = 290+). OpenAI rejects
anything over 128.

Actively firing in production — 13+ errors across multiple agents.

## Root Cause
The chat path (line ~2297) correctly passes `loaded_groups=_loaded_groups`.
The headless path (line ~1874) omits it entirely.

## Fix
In `run_turn`, pass `loaded_groups=set()` to `_build_pydantic_ai_tools`.
This gives headless turns only CORE_TOOLS (25 tools) plus whatever the
caller explicitly requests via the `tools` parameter — which is exactly
what `allow_tools` already handles.

One-line change:
```python
# Line ~1874, runtime.py
pai_tools: list[Tool] = self._build_pydantic_ai_tools(
    exclude_plugins=disabled_plugins,
    allow_tools=set(tools) if tools is not None else None,
    exclude_chat_only=True,
    loaded_groups=set(),  # ADD THIS — headless gets core only
)
```

## Verification
- Existing dojo tests must still pass (headless turns still work)
- A headless turn should produce ≤128 tools even for agents with many plugins
- The `tools` allowlist parameter should still override (caller can name specific tools)

## Rollback
Remove the `loaded_groups=set()` kwarg — single line revert.
