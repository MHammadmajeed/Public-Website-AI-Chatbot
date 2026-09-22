from app.leads.state import (
    COLLECTING,
    COMPLETED,
    DECLINED,
    NOT_STARTED,
    OFFERED,
    decide,
    extract_fields,
    extract_optional_fields,
    is_affirmative,
    is_negative,
)


def test_pricing_starts_collection_and_explains_scope():
    d = decide(NOT_STARTED, {}, "How much does a chatbot cost?", "pricing")
    assert d.state == COLLECTING
    assert "depends on the scope" in d.reply.lower()
    assert "full name" in d.reply.lower()


def test_contact_request_starts_collection():
    d = decide(NOT_STARTED, {}, "I want to start a project", "contact_request")
    assert d.state == COLLECTING
    assert "full name" in d.reply.lower()


def test_normal_question_does_not_start_collection():
    d = decide(NOT_STARTED, {}, "What technologies do you use?", "technology")
    assert d.state == NOT_STARTED
    assert d.reply is None and d.append is None


def test_full_flow_over_multiple_turns():
    d = decide(NOT_STARTED, {}, "How much for a chatbot?", "pricing")
    assert d.state == COLLECTING

    d = decide(d.state, d.data, "Hammad Majeed", "general")
    assert d.data["full_name"] == "Hammad Majeed"
    assert "email" in d.reply.lower()

    bad = decide(d.state, d.data, "not-an-email", "general")
    assert bad.state == COLLECTING
    assert "email" not in bad.data
    assert "valid" in bad.reply.lower()

    d = decide(bad.state, bad.data, "hammad@gmail.com", "general")
    assert d.data["email"] == "hammad@gmail.com"
    assert "phone" in d.reply.lower()

    d = decide(d.state, d.data, "0300 1234567", "general")
    assert d.complete is True
    assert d.state == COMPLETED
    assert d.data["contact_number"] == "03001234567"


def test_question_during_collection_preserves_state():
    data = {"full_name": "Ali Khan"}
    d = decide(COLLECTING, data, "What technologies do you use?", "technology")
    assert d.state == COLLECTING
    assert d.reply is None
    assert "email" in d.append.lower()
    assert d.data == data


def test_pricing_question_during_collection_repeats_request():
    d = decide(COLLECTING, {"full_name": "Ali Khan"}, "How much will it cost?", "pricing")
    assert "depends on the scope" in d.reply.lower()
    assert "email" in d.reply.lower()


def test_decline_stops_collection():
    d = decide(COLLECTING, {}, "no thanks", "general")
    assert d.state == DECLINED


def test_offer_then_yes_starts_collection():
    d = decide(OFFERED, {}, "yes please", "general")
    assert d.state == COLLECTING
    assert "full name" in d.reply.lower()


def test_offer_then_no_declines():
    d = decide(OFFERED, {}, "No thanks", "general")
    assert d.state == DECLINED


def test_completed_lead_is_not_asked_again():
    data = {"full_name": "Ali Khan", "email": "ali@gmail.com", "contact_number": "03001234567"}
    d = decide(COMPLETED, data, "How much will it cost?", "pricing")
    assert d.state == COMPLETED
    assert "already" in d.reply.lower()


def test_all_details_in_one_message():
    ex = extract_fields("Ali Khan, ali@gmail.com, 0300-1234567", {}, "full_name")
    assert ex.error is None
    assert ex.updates == {
        "full_name": "Ali Khan",
        "email": "ali@gmail.com",
        "contact_number": "03001234567",
    }


def test_invalid_email_rejected():
    ex = extract_fields("abc@", {"full_name": "Ali Khan"}, "email")
    assert ex.attempted and ex.error
    assert "email" not in ex.updates


def test_question_is_not_treated_as_an_answer():
    ex = extract_fields("What services do you offer?", {}, "full_name")
    assert not ex.attempted


def test_optional_fields_captured_naturally():
    opt = extract_optional_fields(
        "My company is Acme Traders and we need it within 2 months, budget around $5000"
    )
    assert opt["company_name"] == "Acme Traders"
    assert "2 months" in opt["timeline"]
    assert "5000" in opt["budget_range"]


def test_yes_no_detection():
    assert is_affirmative("Yes please") and is_affirmative("sure")
    assert not is_affirmative("Yusuf Khan")
    assert is_negative("No thanks") and is_negative("not now")
    assert not is_negative("Noah Smith")