#!/usr/bin/env python3
"""Render a step-back prompt from JSON input."""

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


DEFAULT_ROLE = "你是一名擅长从复杂细节中抽象原则，并基于抽象进行稳健推理的助手。"
DEFAULT_OUTPUT_FORMAT = "展示后退问题、抽象依据、简明推理摘要和最终答案。"
DEFAULT_TARGET_INPUT = "等待用户提供待处理内容，或直接使用原始任务中的问题。"
DEFAULT_CONSTRAINTS = "最终答案必须回到原始问题，不要添加与任务无关的解释。"
DEFAULT_TRACE_VISIBILITY = "展示后退问题、抽象依据和简明推理摘要。"
DEFAULT_CONTEXT = "无补充上下文。"
DEFAULT_STEPBACK_QUESTION = "等待抽象阶段生成后退问题。"
DEFAULT_ABSTRACTION = "等待抽象阶段生成相关原则、概念、背景事实或判断标准。"

TEMPLATE_MARKERS = {
    "single-pass": ("<!-- SINGLE_PASS_TEMPLATE_START -->", "<!-- SINGLE_PASS_TEMPLATE_END -->"),
    "abstraction": (
        "<!-- ABSTRACTION_TEMPLATE_START -->",
        "<!-- ABSTRACTION_TEMPLATE_END -->",
    ),
    "reasoning": ("<!-- REASONING_TEMPLATE_START -->", "<!-- REASONING_TEMPLATE_END -->"),
}


def load_payload(path: Path | None) -> dict[str, Any]:
    if path is None:
        payload = json.load(sys.stdin)
    else:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Input JSON must be an object.")
    return payload


def extract_template(path: Path, mode: str) -> str:
    text = path.read_text(encoding="utf-8")
    start_marker, end_marker = TEMPLATE_MARKERS[mode]
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Template markers are missing or invalid for mode `{mode}`.")
    return text[start + len(start_marker) : end].strip()


def format_constraints(value: Any) -> str:
    if value is None:
        return DEFAULT_CONSTRAINTS
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return "\n".join(f"- {item}" for item in items) if items else DEFAULT_CONSTRAINTS
    text = str(value).strip()
    return text if text else DEFAULT_CONSTRAINTS


def pick_text(example: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(example.get(key) or "").strip()
        if value:
            return value
    return ""


def format_examples(value: Any) -> str:
    if value is None:
        return "未检测到用户案例，因此按零样本后退提示生成；请自行生成后退问题和抽象依据。"
    if not isinstance(value, list):
        raise ValueError("`examples` must be a list when provided.")
    if len(value) > 5:
        raise ValueError("`examples` must contain at most 5 items.")
    if not value:
        return "未检测到用户案例，因此按零样本后退提示生成；请自行生成后退问题和抽象依据。"

    blocks: list[str] = []
    for index, example in enumerate(value, start=1):
        if not isinstance(example, dict):
            raise ValueError(f"Example {index} must be an object.")
        original = pick_text(example, "original", "original_question", "question", "input")
        stepback_question = pick_text(example, "stepback_question", "step_back_question")
        abstraction = pick_text(example, "abstraction", "principles", "abstract_answer", "rationale")
        answer = pick_text(example, "answer", "final_answer", "output")
        if not original or not stepback_question or not abstraction:
            raise ValueError(
                f"Example {index} must include original, stepback_question, and abstraction."
            )

        lines = [
            f"#### 案例 {index}",
            "原始问题：",
            '"""',
            original,
            '"""',
            "",
            "后退问题：",
            '"""',
            stepback_question,
            '"""',
            "",
            "抽象依据：",
            '"""',
            abstraction,
            '"""',
        ]
        if answer:
            lines.extend(
                [
                    "",
                    "最终答案：",
                    '"""',
                    answer,
                    '"""',
                ]
            )
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def render_prompt(payload: dict[str, Any], template_path: Path, mode: str) -> str:
    task = str(payload.get("task") or payload.get("instruction") or "").strip()
    if not task:
        raise ValueError("Input JSON must include `task` or `instruction`.")

    template = extract_template(template_path, mode)
    replacements = {
        "{ROLE}": str(payload.get("role") or DEFAULT_ROLE).strip(),
        "{TASK}": task,
        "{TARGET_INPUT}": str(payload.get("target_input") or DEFAULT_TARGET_INPUT).strip(),
        "{OUTPUT_FORMAT}": str(payload.get("output_format") or DEFAULT_OUTPUT_FORMAT).strip(),
        "{CONSTRAINTS}": format_constraints(payload.get("constraints")),
        "{TRACE_VISIBILITY}": str(
            payload.get("trace_visibility") or DEFAULT_TRACE_VISIBILITY
        ).strip(),
        "{EXAMPLES_SECTION}": format_examples(payload.get("examples")),
        "{STEPBACK_QUESTION}": str(
            payload.get("stepback_question")
            or payload.get("step_back_question")
            or DEFAULT_STEPBACK_QUESTION
        ).strip(),
        "{ABSTRACTION}": str(
            payload.get("abstraction")
            or payload.get("principles")
            or payload.get("abstract_answer")
            or DEFAULT_ABSTRACTION
        ).strip(),
        "{CONTEXT}": str(
            payload.get("context")
            or payload.get("retrieved_context")
            or payload.get("supplemental_context")
            or DEFAULT_CONTEXT
        ).strip(),
    }

    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a step-back prompt from JSON.")
    parser.add_argument("input_json", help="Path to a JSON payload, or '-' to read stdin.")
    parser.add_argument(
        "--mode",
        choices=sorted(TEMPLATE_MARKERS),
        default=None,
        help="Prompt mode. Defaults to payload `mode` or single-pass.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets" / "template.md",
    )
    args = parser.parse_args()

    input_json = None if args.input_json == "-" else Path(args.input_json)
    payload = load_payload(input_json)
    mode = args.mode or str(payload.get("mode") or "single-pass").strip()
    if mode not in TEMPLATE_MARKERS:
        raise ValueError(f"`mode` must be one of: {', '.join(sorted(TEMPLATE_MARKERS))}.")
    print(render_prompt(payload, args.template, mode))


if __name__ == "__main__":
    main()
