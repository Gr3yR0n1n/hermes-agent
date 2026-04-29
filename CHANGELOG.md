# Changelog

## [feat/sultanate-optimizations] — 2026-04-28

### Performance

- **Disable Qwen3 thinking mode** (`config.yaml`): Added `extra_body.chat_template_kwargs.enable_thinking: false`. Eliminates multi-thousand-token hidden `<think>` blocks that caused 9-minute response times. Reduces latency to seconds.

- **vLLM prefix caching** (`agrabah/vllm/vllm.service`): Added `--enable-prefix-caching`. KV cache is reused across turns when the system prompt prefix is stable. Confirmed active in vLLM logs (`enable_prefix_caching=True`).

- **Move session timestamp to end of system message** (`run_agent.py`): Session metadata (timestamp, session ID, model) was previously injected mid-system-prompt via `_build_system_prompt`, busting the vLLM prefix cache on every new session. It is now stored in `_session_meta_str` and appended at API-call time, after all stable content (SOUL.md + context). The full stable prefix is now cacheable across session restarts.

- **Signal SSE reconnect delay** (`gateway/platforms/signal.py`): Reduced initial reconnect delay from 2.0s → 0.5s and max backoff from 60s → 30s. Faster reattach when signal-cli bounces.

### New Tools

- **`tools/qr_tool.py`** (`qr_code` tool): Generates a QR code from a URL and returns it as Unicode half-block art in the tool result JSON. Used for Signal device linking. Falls back to `qrencode` CLI if the `qrcode` Python library is unavailable.

### Bug Fixes

- Removed invalid `--disable-log-requests` flag from `agrabah/vllm/vllm.service` (not supported in vLLM 0.19).
