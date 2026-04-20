from app.mock_rag import retrieve


def test_retrieve_supports_vietnamese_refund_query() -> None:
    docs = retrieve("Tôi muốn hoàn tiền cho đơn hàng bị lỗi.")
    assert any("Hoan tien" in doc or "Refunds" in doc for doc in docs)


def test_retrieve_supports_vietnamese_shipping_query() -> None:
    docs = retrieve("Cho tôi hỏi phí vận chuyển và thời gian giao hàng.")
    assert any("Van chuyen" in doc or "shipping" in doc.lower() for doc in docs)
