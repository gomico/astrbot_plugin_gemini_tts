from utils.command_parser import parse_gemini_tts_command


def test_command_without_style_preserves_text():
    assert parse_gemini_tts_command("/GEMINITTS hello") == ("hello", None)


def test_command_preserves_spaces_and_inline_tags():
    assert parse_gemini_tts_command(
        "/GEMINITTS 你好  世界 <short pause> 测试&&cheerful"
    ) == ("你好  世界 <short pause> 测试", "cheerful")


def test_command_uses_last_delimiter():
    assert parse_gemini_tts_command("/GEMINITTS a&&b&&soft") == ("a&&b", "soft")
