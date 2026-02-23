from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VerificationResult:
    ok: bool
    command: str
    stdout: str
    stderr: str
    returncode: int


class CodeVerifier:
    def __init__(self, python_bin: str = "python3") -> None:
        self.python_bin = python_bin

    def verify_python(self, code: str, test_code: str | None = None) -> VerificationResult:
        with tempfile.TemporaryDirectory(prefix="smart_verify_") as td:
            root = Path(td)
            main_file = root / "candidate.py"
            main_file.write_text(code, encoding="utf-8")

            command = f"{self.python_bin} {main_file.name}"
            test_file = None
            if test_code:
                test_file = root / "test_candidate.py"
                test_file.write_text(test_code, encoding="utf-8")
                command = f"{self.python_bin} -m pytest -q {test_file.name}"

            proc = subprocess.run(
                command,
                cwd=root,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return VerificationResult(
                ok=proc.returncode == 0,
                command=command,
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
            )
