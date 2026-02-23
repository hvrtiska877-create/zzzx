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
    def __init__(self, python_bin: str = "python3", timeout_sec: int = 120) -> None:
        self.python_bin = python_bin
        self.timeout_sec = timeout_sec

    def verify_python(self, code: str, test_code: str | None = None) -> VerificationResult:
        with tempfile.TemporaryDirectory(prefix="smart_verify_") as td:
            root = Path(td)
            main_file = root / "candidate.py"
            main_file.write_text(code, encoding="utf-8")

            if test_code:
                test_file = root / "test_candidate.py"
                test_file.write_text(test_code, encoding="utf-8")
                cmd = [self.python_bin, "-m", "pytest", "-q", test_file.name]
            else:
                cmd = [self.python_bin, main_file.name]

            proc = subprocess.run(
                cmd,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=self.timeout_sec,
            )
            return VerificationResult(
                ok=proc.returncode == 0,
                command=" ".join(cmd),
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
            )
