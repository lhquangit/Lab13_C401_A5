from __future__ import annotations

import unicodedata


def normalize_text(text: str) -> str:
    lowered = text.strip().lower()
    normalized = unicodedata.normalize("NFKD", lowered)
    collapsed = "".join(char for char in normalized if not unicodedata.combining(char))
    return collapsed.replace("đ", "d")
