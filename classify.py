"""Clothing type classification from a photo (OpenAI vision)."""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.request
from typing import Optional, Sequence

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.environ.get("OPENAI_VISION_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
# Off by default — set FEATURE_TYPE_SUGGEST=1 and OPENAI_API_KEY to enable.
FEATURE_TYPE_SUGGEST = os.environ.get("FEATURE_TYPE_SUGGEST", "0").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def is_enabled() -> bool:
    return FEATURE_TYPE_SUGGEST and bool(OPENAI_API_KEY)


def _normalize(label: str, allowed: Sequence[str]) -> Optional[str]:
    raw = (label or "").strip().strip('"').strip("'")
    if not raw:
        return None
    by_lower = {a.lower(): a for a in allowed}
    if raw.lower() in by_lower:
        return by_lower[raw.lower()]
    # common synonyms
    aliases = {
        "tee": "T-shirt",
        "t shirt": "T-shirt",
        "tshirt": "T-shirt",
        "top": "Shirt",
        "blouse": "Shirt",
        "hoodie": "Sweater",
        "sweatshirt": "Sweater",
        "coat": "Jacket",
        "blazer": "Jacket",
        "trousers": "Pants",
        "denim": "Jeans",
        "sneakers": "Shoes",
        "boots": "Shoes",
        "heels": "Shoes",
        "cap": "Hat",
        "beanie": "Hat",
        "scarf": "Accessory",
        "bag": "Accessory",
        "belt": "Accessory",
    }
    key = raw.lower().replace("-", " ").replace("_", " ")
    if key in aliases and aliases[key] in allowed:
        return aliases[key]
    for a in allowed:
        if a.lower() in key or key in a.lower():
            return a
    return None


def classify_clothing(
    image_bytes: bytes,
    content_type: str,
    allowed: Sequence[str],
) -> Optional[str]:
    """Return one allowed type label, or None if disabled / failed."""
    if not OPENAI_API_KEY or not image_bytes:
        return None
    mime = (content_type or "image/jpeg").split(";")[0].strip() or "image/jpeg"
    if mime not in {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}:
        mime = "image/jpeg"
    b64 = base64.b64encode(image_bytes).decode("ascii")
    types_list = ", ".join(allowed)
    prompt = (
        "You identify a single clothing item in a photo for a closet app. "
        f"Reply with exactly one label from this list and nothing else: {types_list}. "
        "If unsure, reply Other."
    )
    body = {
        "model": OPENAI_MODEL,
        "temperature": 0,
        "max_tokens": 20,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "low"},
                    },
                ],
            }
        ],
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None
    try:
        text = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None
    if not isinstance(text, str):
        return None
    # first line / first token that looks like a label
    candidate = text.strip().splitlines()[0]
    candidate = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", candidate)
    return _normalize(candidate, allowed) or _normalize(text, allowed)
