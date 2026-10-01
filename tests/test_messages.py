from types import SimpleNamespace

from utils.messages import has_record, plain_text, replace_plain_components


class Plain:
    def __init__(self, text):
        self.text = text


class Record:
    pass


def test_plain_text_and_safe_replacement():
    chain = [SimpleNamespace(kind="image"), Plain("hello"), Plain(" world")]
    assert plain_text(chain) == "hello world"
    record = Record()
    assert replace_plain_components(chain, record)
    assert chain[0].__class__.__name__ == "SimpleNamespace"
    assert chain[1] is record


def test_existing_record_is_a_guard():
    assert has_record([Record()])
