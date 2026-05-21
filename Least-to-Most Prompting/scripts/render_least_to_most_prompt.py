#!/usr/bin/env python3
"""Render a zero-shot least-to-most prompt from JSON input."""

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


DEFAULT_ROLE = "你是一名擅长将复杂任务拆解为有序子问题并逐步求解的推理助手。"
DEFAULT_OUTPUT_FORMAT = "展示问题拆解、子问题有序解答和最终答案。"
DEFAULT_TARGET_INPUT = "等待用户提供待处理内容，或直接使用原始任务中的问题。"
DEFAULT_CONSTRAINTS = "不要添加与任务无关的解释。"
DEFAULT_TRACE_VISIBILITY = "展示问题拆解和子问题答案。"

TEMPLATE_MARKERS = {
    "single-pass": ("<!-- SINGLE_PASS_TEMPLATE_START -->", "<!-- SINGLE_PASS_TEMPLATE_END -->"),
    "decomposition": (
        "<!-- DECOMPOSITION_TEMPLATE_START -->",
        "<!-- DECOMPOSITION_TEMPLATE_END -->",
    ),
    "solution": ("<!-- SOLUTION_TEMPLATE_START -->", "<!-- SOLUTION_TEMPLATE_END -->"),
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


def format_subquestions(value: Any) -> str:
    if value is None:
        return "等待问题拆解阶段生成。"
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))
    text = str(value).strip()
    return text if text else "等待问题拆解阶段生成。"


def format_answered_context(value: Any) -> str:
    if value is None:
        return "暂无已回答子问题。"
    if isinstance(value, list):
        blocks = []
        for index, item in enumerate(value, start=1):
            if isinstance(item, dict):
                question = str(item.get("subquestion") or item.get("question") or "").strip()
                answer = str(item.get("answer") or "").strip()
                if question or answer:
                    blocks.append(f"{index}. 子问题：{question}\n   答案：{answer}")
            else:
                text = str(item).strip()
                if text:
                    blocks.append(f"{index}. {text}")
        return "\n".join(blocks) if blocks else "暂无已回答子问题。"
    text = str(value).strip()
    return text if text else "暂无已回答子问题。"


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
        "{SUBQUESTIONS}": format_subquestions(payload.get("subquestions")),
        "{ANSWERED_CONTEXT}": format_answered_context(payload.get("answered_subquestions")),
        "{NEXT_SUBQUESTION}": str(
            payload.get("next_subquestion") or "等待指定当前子问题。"
        ).strip(),
    }

    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a zero-shot least-to-most prompt.")
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
