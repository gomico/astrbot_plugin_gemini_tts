from utils.style import (
    DEFAULT_LANGUAGE_GUIDANCE,
    normalize_style_selection,
    resolve_style,
    style_templates,
)


def test_preset_and_custom_style():
    assert resolve_style("natural") == (
        "natural, conversational, and relaxed\n" + DEFAULT_LANGUAGE_GUIDANCE
    )
    assert resolve_style("cheerful", {"cheerful": "bright custom"}) == (
        "bright custom\n" + DEFAULT_LANGUAGE_GUIDANCE
    )
    assert resolve_style("softly, nervous") == "softly, nervous"


def test_empty_behavior_differs_by_entry_point():
    assert resolve_style(None, empty_behavior="none") is None
    assert resolve_style("", empty_behavior="natural") == (
        "natural, conversational, and relaxed\n" + DEFAULT_LANGUAGE_GUIDANCE
    )


def test_language_guidance_can_be_customized_or_disabled():
    assert resolve_style("natural", language_guidance="Use standard British English.").endswith(
        "Use standard British English."
    )
    assert resolve_style("natural", language_guidance="") == "natural, conversational, and relaxed"


def test_style_templates_only_merges_style_overrides():
    assert style_templates(None)["natural"] == "natural, conversational, and relaxed"


def test_invalid_classifier_output_falls_back_to_natural():
    assert normalize_style_selection("not-a-preset") == "natural"
