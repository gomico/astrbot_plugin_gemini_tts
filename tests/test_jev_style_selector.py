import asyncio
from unittest.mock import patch

from style_selectors.jev import (
    DEFAULT_JEV_STYLES,
    JevStyleSelector,
    build_jev_payload,
    normalize_jev_styles,
    parse_jev_style,
)


def test_jev_styles_have_safe_defaults_and_keep_natural():
    assert "whispering" not in DEFAULT_JEV_STYLES
    assert "sarcastic" not in DEFAULT_JEV_STYLES
    assert normalize_jev_styles(["excited"]) == ("natural", "excited")
    assert normalize_jev_styles([]) == DEFAULT_JEV_STYLES


def test_jev_payload_and_confidence_fallback():
    payload = build_jev_payload("太好了！", ("natural", "excited"), "jev-latest")
    assert payload["model"] == "jev-latest"
    assert payload["questions"]["style"]["criteria"] == {
        "natural": "Neutral, informational, conversational, or emotionally ambiguous.",
        "excited": "Strong anticipation, surprise, enthusiasm, or high energy.",
    }

    response = {
        "answers": {
            "style": {"choice": "excited", "confidence": 0.9}
        }
    }
    assert parse_jev_style(response, ("natural", "excited"), 0.7) == "excited"
    assert parse_jev_style(response, ("natural", "excited"), 0.95) == "natural"


def test_jev_selector_uses_standard_api_response():
    selector = JevStyleSelector(
        "test-key",
        base_url="https://api.typesafe.ai",
        styles=["natural", "cheerful"],
    )
    response = {
        "answers": {
            "style": {"choice": "cheerful", "confidence": 0.8}
        }
    }
    with patch("style_selectors.jev._post_json", return_value=response) as post:
        assert asyncio.run(selector.select(None, "欢迎回来！")) == "cheerful"

    assert post.call_args.args[0] == "https://api.typesafe.ai/v1/systemone"
    assert post.call_args.args[1] == "test-key"
