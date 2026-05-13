#!/usr/bin/env python3
"""Render a zero-shot prompt from JSON input."""

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


DEFAULT_ROLE = "你是一名严谨的任务执行助手。"
DEFAULT_OUTPUT_FORMAT = "按照用户要求的结构、字段、语言和长度输出。"
DEFAULT_TARGET_INPUT = "等待用户提供待处理内容。"
DEFAULT_CONSTRAINTS = "不要添加与任务无关的解释。"
DEFAULT_FORMAT_EXAMPLE = "无；如需格式骨架，请在 output_format 中说明。"


def load_payload(path: Path | None) -> dict[str, Any]:
    if path is None:
        payload = json.load(sys.stdin)
    else:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Input JSON must be an object.")
    return payload


def extract_template(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start_marker = "<!-- PROMPT_TEMPLATE_START -->"
    end_marker = "<!-- PROMPT_TEMPLATE_END -->"
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Template markers are missing or invalid.")
    block = text[start + len(start_marker) : end].strip()
    if block.startswith("```markdown"):
        block = block.removeprefix("```markdown").strip()
    if block.endswith("```"):
        block = block[:-3].strip()
    return block


def format_constraints(value: Any) -> str:
    if value is None:
        return DEFAULT_CONSTRAINTS
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return "\n".join(f"- {item}" for item in items) if items else DEFAULT_CONSTRAINTS
    text = str(value).strip()
    return text if text else DEFAULT_CONSTRAINTS


def render_prompt(payload: dict[str, Any], template_path: Path) -> str:
    task = str(payload.get("task") or payload.get("instruction") or "").strip()
    if not task:
        raise ValueError("Input JSON must include `task` or `instruction`.")
    role = str(payload.get("role") or DEFAULT_ROLE).strip()
    responsibility = str(payload.get("responsibility") or task).strip()
    role_line = f"{role}，负责{responsibility}" if not role.endswith("。") else role[:-1] + f"，负责{responsibility}"
    template = extract_template(template_path)
    replacements = {
        "你是一名{角色}，负责{任务职责}。": role_line + "。",
        "{明确的任务说明}": task,
        "{格式、字段、数量、语言、风格、禁止项}": str(
            payload.get("output_format") or DEFAULT_OUTPUT_FORMAT
        ).strip(),
        "{可选：只展示格式骨架，不展示任务级输入/输出示例}": str(
            payload.get("format_example") or DEFAULT_FORMAT_EXAMPLE
        ).strip(),
        "{用户输入的文本}": str(payload.get("target_input") or DEFAULT_TARGET_INPUT).strip(),
    }
    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    constraints = format_constraints(payload.get("constraints"))
    if constraints:
        rendered += f"\n\n### 约束条件\n{constraints}"
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a zero-shot prompt from JSON.")
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
