from privacy_detector import detect_sensitive_information


def ocr(text, confidence=0.98, bbox=(10, 10, 300, 40)):
    return {"text": text, "confidence": confidence, "bbox": bbox}


def test_email_detection():
    results = detect_sensitive_information([ocr("Contact example@gmail.com")])
    assert [item.category for item in results] == ["EMAIL"]


def test_phone_detection():
    results = detect_sensitive_information([ocr("Call +91 9876543210")])
    assert any(item.category == "PHONE" for item in results)


def test_url_detection():
    results = detect_sensitive_information([ocr("https://example.com/path")])
    assert any(item.category == "URL" for item in results)


def test_bare_domain_detection():
    results = detect_sensitive_information([ocr("Visit example.com today")])
    assert any(item.category == "URL" for item in results)


def test_normal_text_is_not_sensitive():
    assert detect_sensitive_information([ocr("The weather is clear today")]) == []


def test_empty_ocr_results():
    assert detect_sensitive_information([]) == []


def test_multiple_categories():
    results = detect_sensitive_information([ocr("Mail a@sample.org or visit https://sample.org")])
    assert {item.category for item in results} == {"EMAIL", "URL"}


def test_ordinary_numbers_are_not_phone_numbers():
    results = detect_sensitive_information([ocr("Order 12345, quantity 8")])
    assert all(item.category != "PHONE" for item in results)


def test_long_identifier_is_detected_separately_from_phone():
    results = detect_sensitive_information([ocr("ID 123456789012")])
    assert any(item.category == "ID_NUMBER" for item in results)
    assert all(item.category != "PHONE" for item in results)


def test_invalid_box_is_ignored():
    assert detect_sensitive_information([ocr("a@b.com", bbox=(10, 10, 10, 5))]) == []
