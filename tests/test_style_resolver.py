from utils.style import normalize_style_selection, resolve_style


def test_preset_and_custom_style():
    assert resolve_style("natural") == "natural, conversational, and relaxed"
    assert resolve_style("cheerful", {"cheerful": "bright custom"}) == "bright custom"
    assert resolve_style("softly, nervous") == "softly, nervous"


def test_empty_behavior_differs_by_entry_point():
    assert resolve_style(None, empty_behavior="none") is None
    assert resolve_style("", empty_behavior="natural") == "natural, conversational, and relaxed"


def test_invalid_classifier_output_falls_back_to_natural():
    assert normalize_style_selection("not-a-preset") == "natural"
