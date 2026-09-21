from app.leads.validation import (
    validate_contact_number,
    validate_email,
    validate_full_name,
    validate_optional_text,
)


def test_valid_email_is_cleaned():
    r = validate_email("  Ali.Khan@Gmail.com ")
    assert r.ok and r.value == "ali.khan@gmail.com"


def test_malformed_emails_rejected():
    for bad in ["", "abc", "abc@", "@gmail.com", "a@b", "a b@gmail.com", "a..b@gmail.com"]:
        assert not validate_email(bad).ok, bad


def test_placeholder_emails_rejected():
    for bad in ["test@test.com", "abc@example.com", "asdf@gmail.com"]:
        assert not validate_email(bad).ok, bad


def test_phone_valid_and_cleaned():
    assert validate_contact_number("0300-1234567").value == "03001234567"
    assert validate_contact_number("+92 300 1234567").value == "+923001234567"


def test_phone_invalid_rejected():
    for bad in ["", "abc", "12345", "0000000000", "1234567890", "1111111", "+1234567890123456"]:
        assert not validate_contact_number(bad).ok, bad


def test_name_rules():
    assert validate_full_name("Hammad Majeed").ok
    assert validate_full_name("Ali").ok
    for bad in ["", "test", "12345", "A", "john doe"]:
        assert not validate_full_name(bad).ok, bad


def test_optional_text_never_blocks():
    assert validate_optional_text("company_name", "").ok
    assert validate_optional_text("company_name", None).value is None
    assert len(validate_optional_text("project_summary", "x" * 5000).value) == 1000