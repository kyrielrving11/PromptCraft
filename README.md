# Prompt Engineering Skills

English | [简体中文](README.zh-CN.md)

This repository provides a set of reusable Codex / Skill templates for common prompt engineering techniques. The goal is not to directly solve the user's task, but to generate high-quality prompts from a user's task, output format, constraints, and optional examples.

## Techniques

| Skill | Best for | Examples required | Behavior when examples are missing |
|---|---|---:|---|
| Zero-Shot Prompting | Clear tasks with role, instruction, context, and output format | No | Generate a zero-shot prompt |
| Few-Shot Prompting | Mimicking input-to-output format, style, or mapping | Optional | Fall back to zero-shot prompting with a short notice |
| Zero-Shot Chain-of-Thought | Tasks that need step-by-step reasoning but have no reasoning examples | No | Generate a zero-shot CoT prompt |
| Few-Shot Chain-of-Thought | Mimicking `question -> reasoning -> answer` examples | Optional | Fall back to zero-shot CoT if complete reasoning examples are missing |
| Least-to-Most Prompting | Decomposing a complex task into ordered subquestions and solving them sequentially | No | Generate a Least-to-Most prompt |
| Step-Back Prompting | Abstracting a detailed task into higher-level principles before solving it | Optional | Fall back to zero-shot Step-Back prompting with a short notice |
| Tree of Thoughts Prompting | Exploring, evaluating, pruning, and merging multiple candidate paths | Optional | Fall back to zero-shot Tree-of-Thought prompting with a short notice |

## Why This Exists

This project is useful as an open-source template library because it:

1. Turns prompt engineering papers and techniques into practical, reusable Skills.
2. Standardizes input fields, example formats, and zero-shot fallback behavior.
3. Includes templates, samples, and CLI render scripts for learning, testing, and local integration.

The intended positioning is: **a bilingual prompt engineering Skill template library, especially friendly to Chinese users while still usable globally.**

## Repository Structure

```text
prompt-engineering-skills/
  零样本提示/
    SKILL.md
    assets/template.md
    assets/sample.md
    scripts/render_zero_shot_prompt.py
  少样本提示/
  零样本思维链/
  少样本思维链/
  最少到最多提示/
  后退提示/
  思维树提示/
```

Each folder is an independent Skill:

- `SKILL.md`: trigger description, workflow, and input requirements.
- `assets/template.md`: prompt template and technique-specific rules.
- `assets/sample.md`: sample outputs for reference; these should not be automatically mixed into user prompts.
- `scripts/*.py`: optional CLI render script that turns JSON input into a prompt.

## Quick Start

In a Codex / Skill environment, users can ask naturally:

```text
Use few-shot prompting to create a prompt for customer-support intent extraction.
Output JSON with fields: intent, sentiment, urgency.

Example:
Input: I have waited three days and still have not received my refund.
Output: {"intent":"check refund status","sentiment":"frustrated","urgency":"medium"}
```

The Skill will generate a ready-to-use prompt.

If examples are missing, optional-example Skills do not ask follow-up questions. They automatically generate the zero-shot version and include a short notice such as:

```text
No user examples were detected, so this prompt is generated in zero-shot mode.
```

## CLI Usage

Use UTF-8 JSON files as input:

```bash
python -X utf8 零样本提示/scripts/render_zero_shot_prompt.py input.json
python -X utf8 少样本提示/scripts/render_few_shot_prompt.py input.json
python -X utf8 零样本思维链/scripts/render_zero_shot_cot_prompt.py input.json
python -X utf8 少样本思维链/scripts/render_few_shot_cot_prompt.py input.json
python -X utf8 最少到最多提示/scripts/render_least_to_most_prompt.py input.json
python -X utf8 后退提示/scripts/render_step_back_prompt.py input.json
python -X utf8 思维树提示/scripts/render_tree_of_thought_prompt.py input.json
```

Reading JSON from stdin is also supported:

```bash
python -X utf8 少样本提示/scripts/render_few_shot_prompt.py -
```

On Windows, if your terminal shows garbled Chinese text, try:

```powershell
$env:PYTHONUTF8 = "1"
python -X utf8 .\少样本提示\scripts\render_few_shot_prompt.py .\input.json
```

The scripts also configure `stdin`, `stdout`, and `stderr` as UTF-8 internally.

## Common Input Fields

| Field | Type | Description |
|---|---|---|
| `task` / `instruction` | string | The task for which a prompt should be generated. Required. |
| `role` | string | Optional role used in the generated prompt. |
| `target_input` | string | Optional target content or placeholder. |
| `output_format` | string | Optional final output structure, fields, language, length, or code format. |
| `constraints` | string / list | Optional constraints, style requirements, or forbidden behavior. |
| `examples` | list | Optional examples. The required schema depends on the technique. |

## Technique-Specific Formats

### 1. Zero-Shot Prompting

Use this when there are no examples and the task can be described through instructions and output requirements.

```json
{
  "task": "Extract action items from meeting notes",
  "role": "You are a precise meeting-notes assistant",
  "target_input": "{meeting notes}",
  "output_format": "Return a Markdown table with columns: item, owner, due_date.",
  "constraints": ["Use null for missing fields", "Do not add explanations"]
}
```

No `examples` field is needed.

### 2. Few-Shot Prompting

Use this when the model should imitate input-to-output mappings, formatting, labels, or style.

Example schema:

```json
{
  "input": "User-provided example input",
  "reasoning": "Optional public rationale. Do not include hidden chain-of-thought.",
  "output": "Expected example output"
}
```

Full input example:

```json
{
  "task": "Extract customer intent and sentiment from support messages",
  "role": "You are a precise information extraction assistant",
  "examples": [
    {
      "input": "Customer: I have waited three days and still have not received my refund.",
      "reasoning": "The customer is asking about refund status and expresses frustration.",
      "output": "{\"intent\":\"check refund status\",\"sentiment\":\"frustrated\"}"
    }
  ],
  "target_input": "{customer message}",
  "output_format": "Return JSON only, with fields: intent, sentiment.",
  "constraints": ["Do not explain", "Use null for missing fields"]
}
```

Rules:

- `examples` may be omitted.
- If provided, use 1 to 5 examples.
- Each valid example must include `input` and `output`.
- `reasoning` is optional and should be a public, concise rationale only.
- If no examples are detected, the renderer falls back to zero-shot prompting.

### 3. Zero-Shot Chain-of-Thought

Use this when there are no reasoning examples but the task benefits from step-by-step reasoning.

```json
{
  "task": "Solve elementary math word problems",
  "role": "You are a careful math tutor",
  "target_input": "{problem}",
  "output_format": "First give concise reasoning, then the final answer.",
  "constraints": ["Use at most 5 reasoning steps", "Put the final answer on its own line"]
}
```

No `examples` field is needed.

### 4. Few-Shot Chain-of-Thought

Use this when the model should imitate examples with the structure `question -> reasoning -> final answer`.

Example schema:

```json
{
  "input": "Example question",
  "reasoning": "Example reasoning. Required for few-shot CoT.",
  "output": "Example final answer"
}
```

Aliases are supported:

- `question` instead of `input`
- `answer` instead of `output`
- `rationale` instead of `reasoning`

Full input example:

```json
{
  "task": "Solve elementary math word problems",
  "role": "You are a careful math tutor",
  "examples": [
    {
      "input": "Ming has 5 pencils and buys 2 boxes. Each box has 3 pencils. How many pencils does he have now?",
      "reasoning": "Ming starts with 5 pencils. 2 boxes with 3 pencils each add 2 × 3 = 6 pencils. The total is 5 + 6 = 11.",
      "output": "11"
    }
  ],
  "target_input": "{math word problem}",
  "output_format": "First output reasoning, then final answer.",
  "constraints": ["Keep reasoning concise", "Put final answer on its own line"]
}
```

Rules:

- `examples` may be omitted.
- If provided, use 1 to 5 examples.
- A complete few-shot CoT example must include `input`, `reasoning`, and `output`.
- If reasoning is missing, the renderer does not invent reasoning examples; it falls back to zero-shot CoT.

### 5. Least-to-Most Prompting

Use this when a complex task should first be decomposed into ordered subquestions and then solved sequentially.

```json
{
  "task": "Analyze a complex business problem and produce a decision recommendation",
  "role": "You are an analyst skilled at decomposition and step-by-step reasoning",
  "target_input": "{user problem}",
  "output_format": "Output problem decomposition, ordered subquestion answers, and final answer.",
  "constraints": ["Subquestions must be ordered", "Later answers may reference earlier answers"]
}
```

No `examples` field is needed.

Optional modes:

```bash
python -X utf8 最少到最多提示/scripts/render_least_to_most_prompt.py input.json --mode decomposition
python -X utf8 最少到最多提示/scripts/render_least_to_most_prompt.py input.json --mode solution
```

For `solution` mode, you can additionally provide:

```json
{
  "subquestions": ["Subquestion 1", "Subquestion 2"],
  "answered_subquestions": [
    {
      "subquestion": "Subquestion 1",
      "answer": "Answer to subquestion 1"
    }
  ],
  "next_subquestion": "The current subquestion to answer"
}
```

### 6. Step-Back Prompting

Use this when a task is detailed, multi-hop, or likely to be derailed by local details. The prompt first abstracts to a higher-level concept, principle, formula, factual scope, or decision framework, then returns to the original question.

Example schema:

```json
{
  "original": "Original detailed question",
  "stepback_question": "A higher-level and more general question",
  "abstraction": "Abstract answer, principle, concept, background fact, or framework",
  "answer": "How the abstraction is applied back to the original question"
}
```

Full input example:

```json
{
  "task": "Answer a complex policy question",
  "role": "You are an assistant skilled at abstraction and robust reasoning",
  "target_input": "{user question}",
  "output_format": "First output the step-back question and abstract basis, then the final answer.",
  "examples": [
    {
      "original": "A detailed question",
      "stepback_question": "A higher-level, more general question",
      "abstraction": "Relevant principles, concepts, background facts, or generic framework",
      "answer": "How to use the abstraction to answer the original question"
    }
  ],
  "constraints": ["The final answer must return to the original question", "Do not add irrelevant explanation"]
}
```

Rules:

- `examples` may be omitted.
- If provided, use up to 5 examples.
- Examples demonstrate how to step back and abstract; they should not override the current task.
- If no examples are detected, the renderer falls back to zero-shot Step-Back prompting.

Optional modes:

```bash
python -X utf8 后退提示/scripts/render_step_back_prompt.py input.json --mode abstraction
python -X utf8 后退提示/scripts/render_step_back_prompt.py input.json --mode reasoning
```

### 7. Tree of Thoughts Prompting

Use this for complex planning, multi-option decisions, creative generation, debugging, constraint satisfaction, or search-like reasoning.

Example schema:

```json
{
  "task": "Example task",
  "branches": ["Candidate branch A", "Candidate branch B", "Candidate branch C"],
  "evaluation": "Evaluation, scoring, or pruning criteria",
  "final": "Final selection or synthesis"
}
```

Full input example:

```json
{
  "task": "Generate a Tree-of-Thought prompt for a complex decision",
  "role": "You are a rigorous multi-path problem-solving assistant",
  "target_input": "{user problem}",
  "output_format": "First output a Tree-of-Thought process table, then the final answer.",
  "examples": [
    {
      "task": "Choose a technical architecture",
      "branches": ["Low-cost option", "High-reliability option", "Fast-launch option"],
      "evaluation": "Prune by feasibility, cost, risk, and goal alignment",
      "final": "Synthesize the high-reliability option with cost-control measures"
    }
  ],
  "branch_count": 3,
  "max_depth": 3,
  "keep_count": 2,
  "search_strategy": "beam",
  "evaluation_criteria": ["correctness", "feasibility", "constraint fit", "risk"],
  "decision_rule": "Choose the highest-scoring path; synthesize complementary branches when useful.",
  "constraints": ["At most 3 candidates per round", "At most 3 rounds", "Keep the final answer concise"]
}
```

Rules:

- `examples` may be omitted.
- If provided, use up to 5 examples.
- Examples demonstrate branch generation, evaluation, pruning, and synthesis style.
- If no examples are detected, the renderer falls back to zero-shot Tree-of-Thought prompting.

Optional styles:

```bash
python -X utf8 思维树提示/scripts/render_tree_of_thought_prompt.py input.json --style structured
python -X utf8 思维树提示/scripts/render_tree_of_thought_prompt.py input.json --style expert-panel
python -X utf8 思维树提示/scripts/render_tree_of_thought_prompt.py input.json --style compact
```

## How to Choose

| User need | Recommended Skill |
|---|---|
| Only task and output format are known | Zero-Shot Prompting |
| The model should imitate input-output examples | Few-Shot Prompting |
| No examples, but reasoning is needed | Zero-Shot Chain-of-Thought |
| There are examples with reasoning and answers | Few-Shot Chain-of-Thought |
| A complex problem should be decomposed first | Least-to-Most Prompting |
| The task should step back to high-level principles first | Step-Back Prompting |
| Multiple paths, plans, experts, or candidates should be compared | Tree of Thoughts Prompting |

## License

MIT. See [LICENSE](LICENSE).

## Contributing

Contributions are welcome:

- New prompt engineering Skills.
- Better example schemas.
- More robust templates.
- Domain-specific prompt examples.
- Improved English or Chinese documentation.

Please keep one principle: **a Skill should help users generate better prompts, not hide fragile automation behind unexplained magic.**

