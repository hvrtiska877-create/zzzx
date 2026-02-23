from __future__ import annotations

import argparse

from .agent import SMARTAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="SMART autonomous Python coding assistant")
    parser.add_argument("prompt", help="Task to solve")
    parser.add_argument("--rounds", type=int, default=3, help="Max repair rounds")
    args = parser.parse_args()

    agent = SMARTAgent()
    result = agent.solve_python_task(args.prompt, max_rounds=args.rounds)

    print("# SMART RESULT\n")
    print("## Python code\n")
    print(result.final_code)
    print("\n## Pytest\n")
    print(result.tests)
    print("\n## Verification\n")
    print(f"ok={result.verification.ok} command={result.verification.command} rc={result.verification.returncode}")
    if result.verification.stdout:
        print("stdout:\n" + result.verification.stdout)
    if result.verification.stderr:
        print("stderr:\n" + result.verification.stderr)


if __name__ == "__main__":
    main()
