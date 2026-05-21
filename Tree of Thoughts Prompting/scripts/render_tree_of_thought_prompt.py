#!/usr/bin/env python3
"""Render a Tree of Thoughts prompt from JSON input."""

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


DEFAULT_ROLE = "你是一名擅长多路径搜索、候选评估和稳健决策的思维树提示助手。"
DEFAULT_OUTPUT_FORMAT = "展示思维树过程表、最终选择和最终答案。"
DEFAULT_TARGET_INPUT = "等待用户提供待处理内容，或直接使用原始任务中的问题。"
DEFAULT_CONSTRAINTS = "不要输出冗长隐藏思维链；只输出可公开的候选摘要、评估理由和最终答案。"
DEFAULT_THOUGHT_UNIT = "一个可评价的候选思路、局部方案或中间状态。"
DEFAULT_SEARCH_STRATEGY = "beam"
DEFAULT_BRANCH_COUNT = 3
DEFAULT_MAX_DEPTH = 3
DEFAULT_KEEP_COUNT = 2
DEFAULT_EVALUATION_CRITERIA = ["正确性", "可行性", "约束匹配", "风险"]
DEFAULT_DECISION_RULE = "选择综合评分最高的分支；若多个优秀分支互补，则综合为一个最终答案。"
DEFAULT_TRACE_VISIBILITY = "展示候选摘要、评分/等级、剪枝原因和最终答案。"
DEFAULT_EXPERT_ROLES = [
    "专家 A：正确性与逻辑一致性",
    "专家 B：反例、风险与约束检查",
    "专家 C：综合、表达与最终决策",
]
DEFAULT_EXAMPLES_SECTION = "未检测到用户案例，因此按零样本思维树提示生成；请自行生成、评估、剪枝并合并候选分支。"

TEMPLATE_MARKERS = {
    "structured": ("<!-- STRUCTURED_TEMPLATE_START -->", "<!-- STRUCTURED_TEMPLATE_END -->"),
    "expert-panel": (
        "<!-- EXPERT_PANEL_TEMPLATE_START -->",
        "<!-- EXPERT_PANEL_TEMPLATE_END -->",
    ),
    "compact": ("<!-- COMPACT_TEMPLATE_START -->", "<!-- COMPACT_TEMPLATE_END -->"),
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


def extract_template(path: Path, style: str) -> str:
    text = path.read_text(encoding="utf-8")
    start_marker, end_marker = TEMPLATE_MARKERS[style]
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Template markers are missing or invalid for style `{style}`.")
    return text[start + len(start_marker) : end].strip()


def format_list(value: Any, default: list[str] | str) -> str:
    if value is None:
        value = default
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return "\n".join(f"- {item}" for item in items) if items else format_list(default, [])
    text = str(value).strip()
    return text if text else format_list(default, [])


def pick_text(example: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(example.get(key) or "").strip()
        if value:
            return value
    return ""


def format_examples(value: Any) -> str:
    if value is None or value == "":
        return DEFAULT_EXAMPLES_SECTION
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        raise ValueError("`examples` must be a list or string when provided.")
    if len(value) > 5:
        raise ValueError("`examples` must contain at most 5 items.")
    if not value:
        return DEFAULT_EXAMPLES_SECTION

    blocks: list[str] = []
    for index, example in enumerate(value, start=1):
        if isinstance(example, str):
            content = example.strip()
            if content:
                blocks.append(f"#### 案例 {index}\n{content}")
            continue
        if not isinstance(example, dict):
            raise ValueError(f"Example {index} must be an object or string.")
        task = pick_text(example, "task", "input", "question", "prompt")
        branches = example.get("branches") or example.get("thoughts") or example.get("candidates") or example.get("experts")
        evaluation = pick_text(example, "evaluation", "scores", "critique", "selection_reason")
        final = pick_text(example, "final", "answer", "output", "decision")

        lines = [f"#### 案例 {index}"]
        if task:
            lines.append(f"- 任务：{task}")
        if branches:
            lines.append("- 候选分支/专家思路：")
            if isinstance(branches, list):
                for branch_index, branch in enumerate(branches, start=1):
                    lines.append(f"  {branch_index}. {branch}")
            else:
                lines.append(f"  {branches}")
        if evaluation:
            lines.append(f"- 评估/剪枝依据：{evaluation}")
        if final:
            lines.append(f"- 最终合并结果：{final}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) if blocks else DEFAULT_EXAMPLES_SECTION


def positive_int(value: Any, default: int, name: str) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"`{name}` must be an integer.") from exc
    if parsed < 1:
        raise ValueError(f"`{name}` must be at least 1.")
    return parsed


def render_prompt(payload: dict[str, Any], template_path: Path, style: str) -> str:
    task = str(payload.get("task") or payload.get("instruction") or "").strip()
    if not task:
        raise ValueError("Input JSON must include `task` or `instruction`.")

    branch_count = positive_int(payload.get("branch_count"), DEFAULT_BRANCH_COUNT, "branch_count")
    max_depth = positive_int(payload.get("max_depth"), DEFAULT_MAX_DEPTH, "max_depth")
    keep_count = positive_int(payload.get("keep_count"), DEFAULT_KEEP_COUNT, "keep_count")
    if keep_count > branch_count:
        keep_count = branch_count

    template = extract_template(template_path, style)
    replacements = {
        "{ROLE}": str(payload.get("role") or DEFAULT_ROLE).strip(),
        "{TASK}": task,
        "{TARGET_INPUT}": str(payload.get("target_input") or DEFAULT_TARGET_INPUT).strip(),
        "{OUTPUT_FORMAT}": str(payload.get("output_format") or DEFAULT_OUTPUT_FORMAT).strip(),
        "{CONSTRAINTS}": format_list(payload.get("constraints"), DEFAULT_CONSTRAINTS),
        "{EXAMPLES_SECTION}": format_examples(payload.get("examples")),
        "{THOUGHT_UNIT}": str(payload.get("thought_unit") or DEFAULT_THOUGHT_UNIT).strip(),
        "{SEARCH_STRATEGY}": str(payload.get("search_strategy") or DEFAULT_SEARCH_STRATEGY).strip(),
        "{BRANCH_COUNT}": str(branch_count),
        "{MAX_DEPTH}": str(max_depth),
        "{KEEP_COUNT}": str(keep_count),
        "{EVALUATION_CRITERIA}": format_list(
            payload.get("evaluation_criteria"), DEFAULT_EVALUATION_CRITERIA
        ),
        "{DECISION_RULE}": str(payload.get("decision_rule") or DEFAULT_DECISION_RULE).strip(),
        "{TRACE_VISIBILITY}": str(
            payload.get("trace_visibility") or DEFAULT_TRACE_VISIBILITY
        ).strip(),
        "{EXPERT_ROLES}": format_list(payload.get("expert_roles"), DEFAULT_EXPERT_ROLES),
    }

    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a Tree of Thoughts prompt from JSON.")
    parser.add_argument("input_json", help="Path to a JSON payload, or '-' to read stdin.")
    parser.add_argument(
        "--style",
        choices=sorted(TEMPLATE_MARKERS),
        default=None,
        help="Prompt style. Defaults to payload `style` or structured.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets" / "template.md",
    )
    args = parser.parse_args()

    input_json = None if args.input_json == "-" else Path(args.input_json)
    payload = load_payload(input_json)
    style = args.style or str(payload.get("style") or "structured").strip()
    if style not in TEMPLATE_MARKERS:
        raise ValueError(f"`style` must be one of: {', '.join(sorted(TEMPLATE_MARKERS))}.")
    print(render_prompt(payload, args.template, style))


if __name__ == "__main__":
    main()
