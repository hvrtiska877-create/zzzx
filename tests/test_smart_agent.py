from smart.agent import SMARTAgent
from smart.research import ResearchClient
from smart.verifier import CodeVerifier


def test_extract_python_block():
    text = """text\n```python\nprint('ok')\n```\nmore"""
    out = SMARTAgent._extract_block(text, "python")
    assert out == "print('ok')"


def test_extract_fallback_text():
    text = "no fenced block"
    out = SMARTAgent._extract_block(text, "python")
    assert out == "no fenced block"


def test_verifier_runs_pytest_successfully():
    verifier = CodeVerifier()
    code = "def add(a, b):\n    return a + b\n"
    tests = "from candidate import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n"
    result = verifier.verify_python(code, tests)
    assert result.ok is True
    assert "pytest" in result.command


def test_gather_handles_missing_google_credentials():
    client = ResearchClient(timeout_sec=0.001)
    snippets = client.gather("python list comprehension", limit_per_source=1)
    assert len(snippets) >= 1
    assert any(s.source == "system" for s in snippets)
