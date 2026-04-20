from __future__ import annotations

import time

from .incidents import STATE
from .text_utils import normalize_text

CORPUS = [
    (
        ("refund", "return", "hoan tien", "doi tra", "tra hang"),
        [
            "Refunds are available within 7 days with proof of purchase.",
            "Hoan tien duoc ap dung trong 7 ngay neu khach hang cung cap bang chung mua hang.",
        ],
    ),
    (
        ("order status", "track", "tracking", "trang thai don hang", "kiem tra don hang", "ma van don"),
        [
            "Customers can check order status, latest shipping checkpoint, and estimated delivery date.",
            "Khach hang co the kiem tra trang thai don hang, diem giao hang gan nhat va du kien giao.",
        ],
    ),
    (
        ("shipping", "delivery", "van chuyen", "giao hang", "phi giao hang"),
        [
            "Standard shipping usually takes 3 to 5 business days depending on the destination.",
            "Van chuyen tieu chuan thuong mat 3 den 5 ngay lam viec tuy dia diem giao hang.",
        ],
    ),
    (
        ("payment", "invoice", "charged", "thanh toan", "hoa don", "bi tru tien"),
        [
            "Payment issues should be checked against invoice status, duplicate charges, and refund timeline.",
            "Su co thanh toan can kiem tra hoa don, giao dich bi tru tien hai lan va thoi gian hoan tien.",
        ],
    ),
    (
        ("policy", "pii", "bao mat", "thong tin nhay cam", "du lieu nhay cam"),
        [
            "Do not expose PII in logs. Use sanitized summaries only.",
            "Khong duoc de lo thong tin nhay cam trong log. Chi ghi tom tat da duoc an danh.",
        ],
    ),
]


def retrieve(message: str) -> list[str]:
    if STATE["tool_fail"]:
        raise RuntimeError("Vector store timeout")
    if STATE["rag_slow"]:
        time.sleep(2.5)
    normalized = normalize_text(message)
    for keywords, docs in CORPUS:
        if any(keyword in normalized for keyword in keywords):
            return docs
    return [
        "No domain document matched. Use general fallback answer.",
        "Khong tim thay tai lieu phu hop. He thong se tra loi theo che do ho tro chung.",
    ]
