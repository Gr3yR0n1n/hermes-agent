"""QR code generation tool.

Renders a URL as a Unicode half-block QR code and returns the art as a string
so it becomes part of the tool result in the model's context window.
"""

import json
import logging

logger = logging.getLogger(__name__)

# ── Schema ────────────────────────────────────────────────────────────────────

QR_SCHEMA = {
    "name": "qr_code",
    "description": (
        "Generate a QR code for a URL and return it as Unicode block art. "
        "The 'art' field in the result contains every line of the QR code — "
        "paste it verbatim into your response so the user can scan it."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL or URI to encode as a QR code.",
            },
        },
        "required": ["url"],
    },
}


# ── Helper ────────────────────────────────────────────────────────────────────

def _render_qr_art(url: str) -> str:
    """Return the QR code as a multi-line Unicode string, or raise ImportError."""
    import qrcode  # type: ignore

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)

    matrix = qr.get_matrix()
    rows = len(matrix)
    TOP_HALF = "\u2580"   # ▀
    BOTTOM_HALF = "\u2584"  # ▄
    FULL_BLOCK = "\u2588"  # █
    EMPTY = " "

    lines: list[str] = []
    for r in range(0, rows, 2):
        chars: list[str] = []
        for c in range(len(matrix[r])):
            top = matrix[r][c]
            bottom = matrix[r + 1][c] if r + 1 < rows else False
            if top and bottom:
                chars.append(FULL_BLOCK)
            elif top:
                chars.append(TOP_HALF)
            elif bottom:
                chars.append(BOTTOM_HALF)
            else:
                chars.append(EMPTY)
        lines.append("".join(chars))
    return "\n".join(lines)


# ── Handler ───────────────────────────────────────────────────────────────────

def qr_tool(url: str) -> str:
    try:
        art = _render_qr_art(url)
        return json.dumps({"art": art, "url": url}, ensure_ascii=False)
    except ImportError:
        # Fall back to qrencode if available
        import subprocess
        try:
            result = subprocess.run(
                ["/usr/local/bin/qrencode", "-t", "UTF8", url],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return json.dumps({"art": result.stdout.rstrip(), "url": url}, ensure_ascii=False)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return json.dumps({"error": "qrcode library not installed; run: pip install qrcode", "url": url})
    except Exception as exc:
        logger.exception("qr_tool failed")
        return json.dumps({"error": str(exc), "url": url})


# ── Registration ──────────────────────────────────────────────────────────────

from tools.registry import registry

registry.register(
    name="qr_code",
    toolset="messaging",
    schema=QR_SCHEMA,
    handler=lambda args, **kw: qr_tool(url=args["url"]),
    emoji="📷",
)
