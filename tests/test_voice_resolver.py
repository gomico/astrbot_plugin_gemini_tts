from utils.voice import resolve_voice


def test_voice_precedence_and_alias_fallback():
    assert resolve_voice() == "Kore"
    assert resolve_voice(custom_voice_alias="subaru", custom_voice_aliases={"subaru": "voice_x"}) == "voice_x"
    assert resolve_voice(
        prebuilt_voice="Puck",
        voice_id_override="voice_override",
        custom_voice_alias="subaru",
        custom_voice_aliases={"subaru": "voice_alias"},
    ) == "voice_override"
    assert resolve_voice(prebuilt_voice="Puck", custom_voice_alias="missing", custom_voice_aliases={}) == "Puck"
