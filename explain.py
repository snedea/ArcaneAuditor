#!/usr/bin/env python3
"""Arcane Auditor + LLM: deterministic rules produce findings, an LLM explains them.

Usage:
    uv run explain.py <path>                          # default: ollama/llama3.2
    uv run explain.py <path> --model gpt-4o           # OpenAI
    uv run explain.py <path> --model anthropic/claude-sonnet-4-6  # Claude
    uv run explain.py <path> --model ollama/llama3.2  # Local Ollama
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


SYSTEM_PROMPT = """\
You are a senior Workday Extend code reviewer. You receive deterministic findings \
from Arcane Auditor (a static analysis tool with 42 rules) as JSON.

Your job:
1. TRIAGE: Group findings by priority. What should the developer fix first and why?
2. EXPLAIN: For each finding, explain why it matters in plain English. \
   Not what the rule says -- why a real developer should care.
3. SUGGEST: For ACTION-severity findings, suggest a concrete fix. \
   For ADVICE-severity findings, explain the trade-off.

Rules:
- Never invent findings that aren't in the JSON.
- Never contradict the tool's output.
- Never say a finding is wrong or should be ignored.
- Be concise. Developers don't read walls of text.
- If the JSON has zero findings, just say the app is clean.
"""


def run_audit(path: str) -> dict | None:
    """Run Arcane Auditor and extract the JSON object from its noisy stdout."""
    result = subprocess.run(
        ["uv", "run", "main.py", "review-app", path, "--format", "json", "--quiet"],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
        cwd=Path(__file__).parent,
    )

    if result.returncode not in (0, 1):
        print(f"Arcane Auditor failed (exit {result.returncode}):", file=sys.stderr)
        print(result.stderr or result.stdout, file=sys.stderr)
        return None

    # The parent tool dumps noise before the JSON. Find the first '{'.
    stdout = result.stdout
    idx = stdout.find("{")
    if idx == -1:
        print("No JSON found in Arcane Auditor output.", file=sys.stderr)
        return None

    decoder = json.JSONDecoder()
    try:
        data, _ = decoder.raw_decode(stdout, idx)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}", file=sys.stderr)
        return None

    return data


def explain(findings_json: dict, model: str) -> str:
    """Send findings to an LLM and return the explanation."""
    from litellm import completion

    user_msg = (
        "Here are the Arcane Auditor findings for a Workday Extend application. "
        "Triage, explain, and suggest fixes.\n\n"
        f"```json\n{json.dumps(findings_json, indent=2)}\n```"
    )

    response = completion(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )

    return response.choices[0].message.content


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Arcane Auditor, then explain findings with an LLM.",
    )
    parser.add_argument("path", help="Path to the Extend app directory or file")
    parser.add_argument(
        "--model",
        default="ollama/llama3.2",
        help="LLM model to use (default: ollama/llama3.2). "
        "Examples: gpt-4o, anthropic/claude-sonnet-4-6, ollama/llama3.2",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Just run the audit and print JSON, skip the LLM",
    )
    args = parser.parse_args()

    # Resolve path so it works from any cwd
    path = str(Path(args.path).resolve())

    findings = run_audit(path)
    if findings is None:
        sys.exit(2)

    if args.json_only:
        print(json.dumps(findings, indent=2))
        sys.exit(0 if findings["summary"]["total_findings"] == 0 else 1)

    try:
        explanation = explain(findings, args.model)
    except ImportError:
        print(
            "litellm is not installed. Run: uv pip install litellm\n"
            "Or use --json-only to skip the LLM.",
            file=sys.stderr,
        )
        sys.exit(2)
    except Exception as e:
        print(f"LLM call failed: {e}", file=sys.stderr)
        print("\nFalling back to raw JSON:\n", file=sys.stderr)
        print(json.dumps(findings, indent=2))
        sys.exit(1)

    print(explanation)

    # Exit code mirrors the audit: 0 = clean, 1 = issues found
    sys.exit(0 if findings["summary"]["total_findings"] == 0 else 1)


if __name__ == "__main__":
    main()
