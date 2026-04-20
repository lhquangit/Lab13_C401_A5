from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_tracking_number() -> None:
    out = scrub_text("tracking number: VN1234ABCD")
    assert "VN1234ABCD" not in out
    assert "REDACTED_TRACKING_NUMBER" in out


def test_scrub_bank_account() -> None:
    out = scrub_text("bank account: 123456789012")
    assert "123456789012" not in out
    assert "REDACTED_BANK_ACCOUNT" in out


def test_scrub_cvv() -> None:
    out = scrub_text("cvv: 123")
    assert "cvv: 123" not in out.lower()
    assert "REDACTED_CVV" in out


def test_scrub_vietnamese_address_and_tracking() -> None:
    out = scrub_text("Địa chỉ: 12 Nguyen Hue, mã vận đơn: VN1234ABCD")
    assert "Nguyen Hue" not in out
    assert "VN1234ABCD" not in out
    assert "REDACTED_ADDRESS_FIELD" in out
    assert "REDACTED_TRACKING_NUMBER" in out
