from __future__ import annotations

import re
from dataclasses import dataclass

from .llm import LLMClient
from .research import ResearchClient
from .verifier import CodeVerifier, VerificationResult


@dataclass
class SMARTResponse:
    final_code: str
    tests: str
    verification: VerificationResult
    rationale: str


class SMARTAgent:
    def __init__(self, llm: LLMClient | None = None, research: ResearchClient | None = None, verifier: CodeVerifier | None = None) -> None:
        self.llm = llm or LLMClient()
        self.research = research or ResearchClient()
        self.verifier = verifier or CodeVerifier()

    @staticmethod
    def _extract_block(text: str, language: str) -> str:
        pattern = rf"```{language}\n(.*?)```"
        match = re.search(pattern, text, flags=re.S)
        if match:
            return match.group(1).strip()
        return text.strip()

    def solve_python_task(self, prompt: str, max_rounds: int = 3) -> SMARTResponse:
        snippets = self.research.gather(prompt)
        context = "\n".join([f"[{s.source}] {s.title} :: {s.snippet} ({s.url})" for s in snippets])

        system = (
            "You are SMART, an autonomous coding assistant. "
            "Return python code and pytest tests in fenced blocks: ```python and ```pytest."
        )

        current_prompt = (
            f"User request:\n{prompt}\n\n"
            f"Web context from free sources (google-alternative, reddit, github):\n{context}\n\n"
            "Write production-ready Python code and tests."
        )

        last_verification: VerificationResult | None = None
        code = ""
        tests = ""
        response_text = ""

        for _ in range(max_rounds):
            response_text = self.llm.chat(system=system, user=current_prompt)
            code = self._extract_block(response_text, "python")
            tests = self._extract_block(response_text, "pytest")
            last_verification = self.verifier.verify_python(code, tests)
            if last_verification.ok:
                break
            current_prompt = (
                f"Fix failing code. Prior attempt failed with:\n"
                f"command: {last_verification.command}\n"
                f"stdout:\n{last_verification.stdout}\n"
                f"stderr:\n{last_verification.stderr}\n"
                "Return corrected python and pytest blocks only."
            )

        assert last_verification is not None
        return SMARTResponse(
            final_code=code,
            tests=tests,
            verification=last_verification,
            rationale=response_text,
        )
