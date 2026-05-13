#!/usr/bin/env python3
"""Render a few-shot prompt from JSON input and the bundled template."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any


def configure_stdio() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


configure_stdio()


DEFAULT_ROLE = "你是一个严谨的少样本任务执行助手。"
DEFAULT_OUTPUT_FORMAT = "按照示例展示的格式输出最终答案。"
DEFAULT_TARGET_INPUT = "等待用户提供目标输入。"
DEFAULT_CONSTRAINTS = "不要输出与任务无关的解释。"
DYNAMIC_SAMPLE_HEADING = "## 动态用户样例库"
ZERO_SHOT_EXAMPLE_NOTICE = "未检测到用户案例，因此按零样本提示生成；请根据任务说明、输出要求和约束自行完成任务，不要依赖示例。"


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
        input_text = str(example.get("input", "")).strip()
        output_text = str(example.get("output", "")).strip()
        reasoning_text = str(
            example.get("reasoning")
            or example.get("reasoning_process")
            or example.get("rationale")
            or ""
        ).strip()
        if not input_text or not output_text:
            continue
        normalized_example = {"input": input_text, "output": output_text}
        if reasoning_text:
            normalized_example["reasoning"] = reasoning_text
        normalized.append(normalized_example)
    return normalized


def format_examples(examples: list[dict[str, str]]) -> str:
    if not examples:
        return ZERO_SHOT_EXAMPLE_NOTICE
    blocks = []
    for index, example in enumerate(examples, start=1):
        lines = [
            f"#### 示例 {index}",
            "输入：",
            '"""',
            example["input"],
            '"""',
        ]
        if example.get("reasoning"):
            lines.extend(
                [
                    "",
                    "推理过程：",
                    '"""',
                    example["reasoning"],
                    '"""',
                ]
            )
        lines.extend(
            [
                "",
                "输出：",
                '"""',
                example["output"],
                '"""',
            ]
        )
        blocks.append("\n".join(lines))
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


def render_prompt(
    payload: dict[str, Any], template_path: Path
) -> tuple[str, str, list[dict[str, str]]]:
    examples = validate_examples(payload)
    example_block = format_examples(examples)
    template = extract_template(template_path)

    instruction = str(payload.get("instruction") or payload.get("task") or "").strip()
    if not instruction:
        raise ValueError("Input JSON must include `task` or `instruction`.")

    replacements = {
        "{ROLE}": str(payload.get("role") or DEFAULT_ROLE).strip(),
        "{INSTRUCTION}": instruction,
        "{FEW_SHOT_EXAMPLES}": example_block,
        "{OUTPUT_FORMAT}": str(payload.get("output_format") or DEFAULT_OUTPUT_FORMAT).strip(),
        "{TARGET_INPUT}": str(payload.get("target_input") or DEFAULT_TARGET_INPUT).strip(),
        "{CONSTRAINTS}": format_constraints(payload.get("constraints")),
    }

    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered, example_block, examples


def markdown_fence(text: str, language: str = "") -> str:
    longest_backtick_run = max(
        (len(match.group(0)) for match in re.finditer(r"`+", text)), default=0
    )
    fence = "`" * max(3, longest_backtick_run + 1)
    suffix = language.strip()
    opening = f"{fence}{suffix}" if suffix else fence
    return f"{opening}\n{text}\n{fence}"


def clean_title(value: Any, fallback: str) -> str:
    title = str(value or "").strip() or fallback
    title = " ".join(title.split())
    return title[:60]


def format_sample_entry(
    payload: dict[str, Any],
    examples: list[dict[str, str]],
    prompt: str,
    sample_title: str | None,
) -> str:
    instruction = str(payload.get("instruction") or payload.get("task") or "").strip()
    title = clean_title(
        sample_title or payload.get("sample_title") or payload.get("title"),
        instruction or "未命名任务",
    )
    role = str(payload.get("role") or DEFAULT_ROLE).strip()
    output_format = str(payload.get("output_format") or DEFAULT_OUTPUT_FORMAT).strip()
    target_input = str(payload.get("target_input") or DEFAULT_TARGET_INPUT).strip()
    constraints = format_constraints(payload.get("constraints"))

    lines = [
        f"## 动态样例：{title}",
        "",
        f"- 记录时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 任务：{instruction}",
        f"- 角色：{role}",
        "",
        "### 用户输入-推理过程-输出示例",
    ]

    for index, example in enumerate(examples, start=1):
        lines.extend(
            [
                "",
                f"#### 示例 {index}",
                "输入：",
                markdown_fence(example["input"], "text"),
            ]
        )
        if example.get("reasoning"):
            lines.extend(
                [
                    "",
                    "推理过程：",
                    markdown_fence(example["reasoning"], "text"),
                ]
            )
        lines.extend(
            [
                "",
                "输出：",
                markdown_fence(example["output"], "text"),
            ]
        )

    lines.extend(
        [
            "",
            "### 输出格式",
            markdown_fence(output_format, "text"),
            "",
            "### 待处理内容占位",
            markdown_fence(target_input, "text"),
            "",
            "### 约束",
            markdown_fence(constraints, "text"),
            "",
            "### 生成的少样本提示 Prompt",
            markdown_fence(prompt, "markdown"),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def should_persist_sample(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def append_dynamic_sample(destination: Path, entry: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing = destination.read_text(encoding="utf-8")
    else:
        existing = "# 少样本提示案例\n"

    chunks: list[str] = []
    if not existing.endswith("\n"):
        chunks.append("\n")
    if DYNAMIC_SAMPLE_HEADING not in existing:
        chunks.append(
            "\n"
            f"{DYNAMIC_SAMPLE_HEADING}\n\n"
            "以下条目由脚本在用户明确要求沉淀样例时追加，用于保存可复用的输入、推理过程和输出示例。\n"
        )
    chunks.append("\n" + entry)

    with destination.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("".join(chunks))


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a few-shot prompt from JSON.")
    parser.add_argument("input_json", help="Path to a JSON payload, or '-' to read stdin.")
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets" / "template.md",
    )
    parser.add_argument("--write-session-sample", type=Path)
    parser.add_argument(
        "--append-to-sample",
        action="store_true",
        help="Append this task and its examples to assets/sample.md as a reusable sample.",
    )
    parser.add_argument(
        "--sample-file",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets" / "sample.md",
        help="Sample library path used with --append-to-sample.",
    )
    parser.add_argument("--sample-title", help="Title for the appended sample entry.")
    args = parser.parse_args()

    input_json = None if args.input_json == "-" else Path(args.input_json)
    payload = load_payload(input_json)
    prompt, example_block, examples = render_prompt(payload, args.template)

    if args.write_session_sample:
        destination = args.write_session_sample.resolve()
        protected_sample = (Path(__file__).resolve().parents[1] / "assets" / "sample.md").resolve()
        if destination == protected_sample:
            raise ValueError("Refusing to overwrite bundled assets/sample.md; use a session file.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(example_block + "\n", encoding="utf-8")

    if (args.append_to_sample or should_persist_sample(payload.get("persist_sample"))) and examples:
        entry = format_sample_entry(payload, examples, prompt, args.sample_title)
        append_dynamic_sample(args.sample_file.resolve(), entry)

    print(prompt)


if __name__ == "__main__":
    main()
