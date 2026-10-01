from utils.auto import should_attempt_auto_tts


def test_probability_boundaries_and_guards():
    assert not should_attempt_auto_tts(True, 0, readable_text=True, already_processed=False, draw=0)
    assert should_attempt_auto_tts(True, 1, readable_text=True, already_processed=False, draw=1)
    assert not should_attempt_auto_tts(True, 1, readable_text=False, already_processed=False, draw=0)
    assert not should_attempt_auto_tts(True, 1, readable_text=True, already_processed=True, draw=0)
    assert not should_attempt_auto_tts(True, 0.5, readable_text=True, already_processed=False, draw=0.5)
    assert should_attempt_auto_tts(True, 0.5, readable_text=True, already_processed=False, draw=0.49)
