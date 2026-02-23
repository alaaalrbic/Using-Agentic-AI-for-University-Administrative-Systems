"""
Utility Functions
"""

import json
from typing import Any


def mcp_to_python(result: Any) -> Any:
    """
    Convert FastMCP result objects to Python primitives (dict/list/str) when possible.
    
    The FastMCP library wraps responses in nested content lists. This helper extracts
    JSON strings and returns them as Python objects.
    """
    if isinstance(result, (dict, list, str)):
        return result
    content = getattr(result, "content", None)
    if not content:
        return None
    parsed = []
    for item in content:
        txt = getattr(item, "text", None)
        if not isinstance(txt, str) or not txt.strip():
            continue
        s = txt.strip()
        try:
            parsed.append(json.loads(s))
        except Exception:
            parsed.append(s)
    if not parsed:
        return None
    return parsed[0] if len(parsed) == 1 else parsed