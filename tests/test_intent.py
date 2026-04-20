from app.main import infer_intent


def test_infer_intent_supports_vietnamese_refund() -> None:
    assert infer_intent("hoan_tien", "Tôi muốn hoàn tiền cho đơn hàng bị lỗi.") == "refund"


def test_infer_intent_supports_vietnamese_order_status() -> None:
    assert infer_intent("support", "Tôi muốn kiểm tra trạng thái đơn hàng và mã vận đơn.") == "order_status"


def test_infer_intent_supports_vietnamese_payment() -> None:
    assert infer_intent("support", "Tôi bị trừ tiền hai lần khi thanh toán.") == "payment"
