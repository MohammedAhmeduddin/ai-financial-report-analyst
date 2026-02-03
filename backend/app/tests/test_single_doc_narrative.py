from app.services.single_doc_narrative import build_single_doc_narrative


def test_single_doc_narrative_with_value():
    text = build_single_doc_narrative(
        question="What is net income?",
        metric_key="net_income",
        metric_value=123.0,
    )
    assert "Net Income" in text
    assert "123" in text


def test_single_doc_narrative_missing_value():
    text = build_single_doc_narrative(
        question="What is net income?",
        metric_key="net_income",
        metric_value=None,
    )
    assert "couldn’t find a numeric value" in text.lower()
