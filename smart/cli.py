from __future__ import annotations

import argparse
from pathlib import Path

from .agent import SMARTAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="SMART autonomous Python coding assistant")
    parser.add_argument("prompt", help="Task to solve")
    parser.add_argument("--rounds", type=int, default=3, help="Max repair rounds")
    parser.add_argument("--out-dir", default="smart_output", help="Directory to write generated files")
    args = parser.parse_args()

    agent = SMARTAgent()
    result = agent.solve_python_task(args.prompt, max_rounds=args.rounds)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "candidate.py").write_text(result.final_code, encoding="utf-8")
    (out_dir / "test_candidate.py").write_text(result.tests, encoding="utf-8")
    (out_dir / "verification.txt").write_text(
        f"ok={result.verification.ok}\n"
        f"command={result.verification.command}\n"
        f"rc={result.verification.returncode}\n\n"
        f"stdout:\n{result.verification.stdout}\n\n"
        f"stderr:\n{result.verification.stderr}\n",
        encoding="utf-8",
    )

    print(f"Saved generated files to: {out_dir.resolve()}")
    print(f"Verification ok={result.verification.ok} command={result.verification.command}")


if __name__ == "__main__":
    main()
