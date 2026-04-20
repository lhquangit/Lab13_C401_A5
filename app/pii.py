from __future__ import annotations

import hashlib
import re

PII_PATTERNS: dict[str, str] = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "phone_vn": r"(?:\+84|0)[ \.-]?\d{3}[ \.-]?\d{3}[ \.-]?\d{3,4}",
    "bank_account": r"(?i)\b(?:bank account|stk|so tai khoan|số tài khoản)\s*[:\-]?\s*\d{8,20}\b",
    "cccd": r"\b\d{12}\b",
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "cvv": r"(?i)\bcvv\s*[:\-]?\s*\d{3,4}\b",
    "tracking_number": r"(?i)\b(?:tracking(?:\s*number)?|ma van don|mã vận đơn|awb)\s*[:#\-]?\s*[A-Z0-9\-]{8,20}\b",
    "passport_vn": r"\b[A-Z]\d{7}\b",
    "address_field": r"(?i)\b(?:address|dia chi|địa chỉ)\s*[:\-]\s*[^,;\n]{6,100}",
}


def scrub_text(text: str) -> str:
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
