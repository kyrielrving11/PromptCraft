#!/usr/bin/env python3
"""Render a few-shot chain-of-thought prompt from JSON input."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def configure_stdio() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


configure_stdio()


DEFAULT_ROLE = "你是一名严谨的多步推理助手。"
DEFAULT_OUTPUT_FORMAT = "先输出推理过程，再输出最终答案。"
DEFAULT_TARGET_INPUT = "等待用户提供目标问题。"
DEFAULT_CONSTRAINTS = "推理过程要简洁，最终答案要单独标记。"
ZERO_SHOT_COT_NOTICE = "未检测到完整用户推理案例，因此按零样本思维链提示生成；请自行进行简明逐步推理，再给出最终答案。"


def load_payload(path: Path | None) -> dict[str, Any]:
    if path is None:
        payload = json.load(sys.stdin)
    else:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Input JSON must be an object.")
    return payload


def validate_examples(payload: dict[str, Any]) -> list[dict[str, str]]:
    examples = payload.get("examples")
    if examples in (None, ""):
        return []
    if not isinstance(examples, list):
        raise ValueError("`examples` must be a list.")
    if len(examples) > 5:
        raise ValueError("`examples` must contain at most 5 items.")
    normalized: list[dict[str, str]] = []
    for index, example in enumerate(examples, start=1):
        if not isinstance(example, dict):
            continue
        input_text = str(example.get("input") or example.get("question") or "").strip()
        reasoning_text = str(example.get("reasoning") or example.get("rationale") or "").strip()
        output_text = str(example.get("output") or example.get("answer") or "").strip()
        if not input_text or not reasoning_text or not output_text:
            continue
        normalized.append(
            {"input": input_text, "reasoning": reasoning_text, "output": output_text}
        )
    return normalized


def format_examples(examples: list[dict[str, str]]) -> str:
    if not examples:
        return ZERO_SHOT_COT_NOTICE
    blocks = []
    for index, example in enumerate(examples, start=1):
        blocks.append(
            "\n".join(
                [
                    f"#### 示例 {index}",
                    "问题：",
                    '"""',
                    example["input"],
                    '"""',
                    "",
                    "推理过程：",
                    '"""',
                    example["reasoning"],
                    '"""',
                    "",
                    "最终答案：",
                    '"""',
                    example["output"],
                    '"""',
                ]
            )
        )
    return "\n\n".join(blocks)


def format_constraints(value: Any) -> str:
    if value is None:
        return DEFAULT_CONSTRAINTS
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return "\n".join(f"- {item}" for item in items) if items else DEFAULT_CONSTRAINTS
    text = str(value).strip()
    return text if text else DEFAULT_CONSTRAINTS


def extract_template(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start_marker = "<!-- PROMPT_TEMPLATE_START -->"
    end_marker = "<!-- PROMPT_TEMPLATE_END -->"
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Template markers are missing or invalid.")
    return text[start + len(start_marker) : end].strip()


def render_prompt(payload: dict[str, Any], template_path: Path) -> str:
    examples = validate_examples(payload)
    instruction = str(payload.get("instruction") or payload.get("task") or "").strip()
    if not instruction:
        raise ValueError("Input JSON must include `task` or `instruction`.")
    replacements = {
        "{ROLE}": str(payload.get("role") or DEFAULT_ROLE).strip(),
        "{INSTRUCTION}": instruction,
        "{FEW_SHOT_COT_EXAMPLES}": format_examples(examples),
        "{OUTPUT_FORMAT}": str(payload.get("output_format") or DEFAULT_OUTPUT_FORMAT).strip(),
        "{TARGET_INPUT}": str(payload.get("target_input") or DEFAULT_TARGET_INPUT).strip(),
        "{CONSTRAINTS}": format_constraints(payload.get("constraints")),
    }
    rendered = extract_template(template_path)
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a few-shot CoT prompt from JSON.")
    parser.add_argument("input_json", help="Path to a JSON payload, or '-' to read stdin.")
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets" / "template.md",
    )
    args = parser.parse_args()

    input_json = None if args.input_json == "-" else Path(args.input_json)
    payload = load_payload(input_json)
    print(render_prompt(payload, args.template))


if __name__ == "__main__":
    main()
