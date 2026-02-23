from smart.agent import SMARTAgent


def test_extract_python_block():
    text = """text\n```python\nprint('ok')\n```\nmore"""
    out = SMARTAgent._extract_block(text, "python")
    assert out == "print('ok')"


def test_extract_fallback_text():
    text = "no fenced block"
    out = SMARTAgent._extract_block(text, "python")
    assert out == "no fenced block"
