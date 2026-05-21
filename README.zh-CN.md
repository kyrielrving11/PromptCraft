# 提示工程技术 Skills

[English](README.md) | 简体中文

这是一组面向 Codex / Skill 工作流的提示工程技术模板。它们的目标不是直接替用户完成任务，而是根据用户的任务、输出格式、约束和可选案例，生成一份可以复制使用的高质量 Prompt。

当前包含 7 类提示工程技术：

| 技术 | 适合场景 | 是否需要案例 | 无案例时行为 |
|---|---|---:|---|
| 零样本提示 | 任务清楚、只需要角色、指令、上下文和输出格式 | 否 | 直接生成零样本 Prompt |
| 少样本提示 | 需要模型模仿输入到输出的格式、风格或映射关系 | 可选 | 退回零样本提示，并说明未检测到案例 |
| 零样本思维链 | 没有推理案例，但任务需要简明逐步推理 | 否 | 直接生成零样本 CoT Prompt |
| 少样本思维链 | 需要模型模仿“问题 -> 推理过程 -> 答案”的推理模式 | 可选 | 没有完整推理案例时退回零样本思维链 |
| 最少到最多提示 | 复杂任务需要先拆成有序子问题，再逐步求解 | 否 | 直接生成 Least-to-Most Prompt |
| 后退提示 | 复杂、多细节任务需要先抽象到高层原则，再回到原题 | 可选 | 退回零样本后退提示，并说明未检测到案例 |
| 思维树提示 | 复杂规划、决策、搜索、创意或排错任务需要多分支探索 | 可选 | 退回零样本思维树提示，并说明未检测到案例 |

## 开源价值

这个项目是有开源意义的，原因有三点：

1. 它把常见提示工程论文方法整理成可复用的 Skill，而不是停留在论文摘要或散落的提示词片段。
2. 它统一了输入结构、案例格式和无案例回退逻辑，用户可以主动选择技术，不需要复杂交互。
3. 它给每个技术都配了模板、样例和渲染脚本，方便学习、测试、二次修改和集成到本地工作流。

更适合的开源定位是：**面向中文用户的提示工程 Skill 模板库**。

## 目录结构

```text
提示工程技术skills/
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

每个文件夹都是一个独立 Skill：

- `SKILL.md`：触发条件、使用规则、输入要求。
- `assets/template.md`：生成 Prompt 的模板和技术规则。
- `assets/sample.md`：示例输出，不应被默认混入用户 Prompt。
- `scripts/*.py`：可选 CLI 渲染脚本，用 JSON 生成 Prompt。

## 快速使用

在 Codex / Skill 环境中，用户可以直接说：

```text
请使用少样本提示，帮我为“客服诉求抽取”生成提示词。
输出格式是 JSON，字段为 诉求、情绪、紧急程度。
案例：
输入：我等了三天还没收到退款。
输出：{"诉求":"查询退款进度","情绪":"不满","紧急程度":"中"}
```

Skill 会生成可直接复制使用的 Prompt。

如果用户没有提供案例，支持可选案例的 Skill 不会追问，会自动生成零样本版本，并在 Prompt 中说明：

```text
未检测到用户案例，因此按零样本提示生成。
```

## CLI 使用

推荐把输入写成 UTF-8 JSON 文件，然后运行对应脚本：

```bash
python -X utf8 零样本提示/scripts/render_zero_shot_prompt.py input.json
python -X utf8 少样本提示/scripts/render_few_shot_prompt.py input.json
python -X utf8 零样本思维链/scripts/render_zero_shot_cot_prompt.py input.json
python -X utf8 少样本思维链/scripts/render_few_shot_cot_prompt.py input.json
python -X utf8 最少到最多提示/scripts/render_least_to_most_prompt.py input.json
python -X utf8 后退提示/scripts/render_step_back_prompt.py input.json
python -X utf8 思维树提示/scripts/render_tree_of_thought_prompt.py input.json
```

也支持从 stdin 读取 JSON：

```bash
python -X utf8 少样本提示/scripts/render_few_shot_prompt.py -
```

Windows 终端如出现中文乱码，建议：

```powershell
$env:PYTHONUTF8 = "1"
python -X utf8 .\少样本提示\scripts\render_few_shot_prompt.py .\input.json
```

脚本内部已经设置 `stdin/stdout/stderr` 为 UTF-8，通常不需要额外配置。

## 通用输入字段

不同技术的 JSON 输入略有差异，但常用字段如下：

| 字段 | 类型 | 说明 |
|---|---|---|
| `task` / `instruction` | string | 用户要生成 Prompt 的任务目标，必填 |
| `role` | string | 可选，模型在生成 Prompt 中扮演的角色 |
| `target_input` | string | 可选，待处理内容或占位符 |
| `output_format` | string | 可选，最终输出结构、字段、语言、长度或代码格式 |
| `constraints` | string / list | 可选，约束条件、禁止事项、风格要求 |
| `examples` | list | 可选，案例；不同技术的案例格式不同 |

## 各技术输入与案例格式

### 1. 零样本提示

适合：没有案例，只希望模型按任务说明和输出格式完成任务。

```json
{
  "task": "从会议记录中提取待办事项",
  "role": "你是一名严谨的会议纪要整理助手",
  "target_input": "{会议记录}",
  "output_format": "输出 Markdown 表格，字段为 事项、负责人、截止时间。",
  "constraints": ["缺失字段填 null", "不要输出解释"]
}
```

不需要 `examples`。

### 2. 少样本提示

适合：希望模型模仿输入到输出的格式、判断口径或写作风格。

案例格式：

```json
{
  "input": "用户提供的示例输入",
  "reasoning": "可选。可公开的简要判断依据，不要写隐藏思维链。",
  "output": "用户期望的示例输出"
}
```

完整输入示例：

```json
{
  "task": "从客服对话中抽取客户诉求和情绪",
  "role": "你是一名严谨的信息抽取助手",
  "examples": [
    {
      "input": "客户：我等了三天还没收到退款。",
      "reasoning": "用户关注退款进度，表达等待过久带来的不满。",
      "output": "{\"诉求\":\"查询退款进度\",\"情绪\":\"不满\"}"
    }
  ],
  "target_input": "{用户输入的客服对话}",
  "output_format": "仅输出 JSON，字段为 诉求、情绪。",
  "constraints": ["不要输出解释", "字段缺失时填 null"]
}
```

规则：

- `examples` 可省略。
- 如果提供案例，数量建议 1-5 个。
- 每个有效案例必须有 `input` 和 `output`。
- `reasoning` 可选，只写可公开的简要依据。
- 无案例时自动退回零样本提示。

### 3. 零样本思维链

适合：没有推理案例，但任务需要逐步推理、计算、判断或排除。

```json
{
  "task": "解决小学数学应用题",
  "role": "你是一名严谨的数学解题助手",
  "target_input": "{用户输入的题目}",
  "output_format": "先输出简明推理过程，再输出最终答案。",
  "constraints": ["推理过程不超过 5 步", "最终答案单独成行"]
}
```

不需要 `examples`。

### 4. 少样本思维链

适合：希望模型模仿一组“问题 -> 推理过程 -> 最终答案”的推理模式。

案例格式：

```json
{
  "input": "示例问题",
  "reasoning": "示例推理过程，必须存在。",
  "output": "示例最终答案"
}
```

也可以使用同义字段：

- `question` 代替 `input`
- `answer` 代替 `output`
- `rationale` 代替 `reasoning`

完整输入示例：

```json
{
  "task": "解决小学数学应用题",
  "role": "你是一名严谨的数学解题助手",
  "examples": [
    {
      "input": "小明有 5 支铅笔，又买了 2 盒，每盒 3 支。他现在有几支铅笔？",
      "reasoning": "小明原来有 5 支。2 盒每盒 3 支，所以新增 2 × 3 = 6 支。总数是 5 + 6 = 11 支。",
      "output": "11"
    }
  ],
  "target_input": "{用户输入的数学应用题}",
  "output_format": "先输出推理过程，再输出最终答案。",
  "constraints": ["推理步骤要简洁", "最终答案单独成行"]
}
```

规则：

- `examples` 可省略。
- 如果提供案例，数量建议 1-5 个。
- 每个完整案例必须有 `input`、`reasoning`、`output`。
- 如果案例缺少 `reasoning`，不会编造推理案例；会按零样本思维链生成。

### 5. 最少到最多提示

适合：复杂任务需要先自上而下拆解成有序子问题，再自下而上逐一解答。

```json
{
  "task": "分析一个复杂商业问题并给出决策建议",
  "role": "你是一名擅长问题拆解和逐步推理的分析助手",
  "target_input": "{用户输入的问题}",
  "output_format": "输出问题拆解、子问题逐一解答、最终答案。",
  "constraints": ["子问题必须有顺序", "后一个子问题可引用前一个答案"]
}
```

不需要 `examples`。

可选模式：

```bash
python -X utf8 最少到最多提示/scripts/render_least_to_most_prompt.py input.json --mode decomposition
python -X utf8 最少到最多提示/scripts/render_least_to_most_prompt.py input.json --mode solution
```

`solution` 模式可额外提供：

```json
{
  "subquestions": ["子问题 1", "子问题 2"],
  "answered_subquestions": [
    {
      "subquestion": "子问题 1",
      "answer": "子问题 1 的答案"
    }
  ],
  "next_subquestion": "当前要回答的子问题"
}
```

### 6. 后退提示

适合：复杂、多细节、容易被局部信息带偏的任务。它先后退到更高层概念、原则、公式、事实范围或判断框架，再回到原题。

案例格式：

```json
{
  "original": "原始问题",
  "stepback_question": "更高层、更通用的问题",
  "abstraction": "抽象答案、原则、概念、背景事实或判断框架",
  "answer": "如何基于抽象回到原题得到最终答案"
}
```

完整输入示例：

```json
{
  "task": "回答复杂政策问题",
  "role": "你是一名擅长抽象原则和稳健推理的助手",
  "target_input": "{用户输入的问题}",
  "output_format": "先输出后退问题和抽象依据，再输出最终答案。",
  "examples": [
    {
      "original": "具体问题",
      "stepback_question": "更高层、更通用的问题",
      "abstraction": "相关原则、概念、背景事实或通用框架",
      "answer": "如何基于抽象回到原题得到答案"
    }
  ],
  "constraints": ["最终答案必须回到原始问题", "不要添加无关解释"]
}
```

规则：

- `examples` 可省略。
- 如果提供案例，数量建议 0-5 个。
- 有案例时用于展示“如何后退抽象”，不覆盖当前任务。
- 无案例时自动退回零样本后退提示。

可选模式：

```bash
python -X utf8 后退提示/scripts/render_step_back_prompt.py input.json --mode abstraction
python -X utf8 后退提示/scripts/render_step_back_prompt.py input.json --mode reasoning
```

### 7. 思维树提示

适合：复杂规划、多方案决策、创意生成、代码排错、约束满足、搜索型推理。

案例格式：

```json
{
  "task": "示例任务",
  "branches": ["候选分支 A", "候选分支 B", "候选分支 C"],
  "evaluation": "评估、评分或剪枝依据",
  "final": "最终选择或合并结果"
}
```

完整输入示例：

```json
{
  "task": "为复杂问题生成思维树提示词",
  "role": "你是一名严谨的多路径问题求解助手",
  "target_input": "{用户输入的问题}",
  "output_format": "先输出思维树过程表，再输出最终答案。",
  "examples": [
    {
      "task": "选择技术方案",
      "branches": ["低成本方案", "高可靠方案", "快速上线方案"],
      "evaluation": "根据可行性、成本、风险和目标一致性剪枝",
      "final": "整合高可靠方案和成本控制策略后形成最终建议"
    }
  ],
  "branch_count": 3,
  "max_depth": 3,
  "keep_count": 2,
  "search_strategy": "beam",
  "evaluation_criteria": ["正确性", "可行性", "约束匹配", "风险"],
  "decision_rule": "选择最高分路径；若两个分支互补，则综合后给出一个答案。",
  "constraints": ["每轮最多 3 个候选", "最多 3 轮", "最终答案必须简洁"]
}
```

规则：

- `examples` 可省略。
- 如果提供案例，数量建议 0-5 个。
- 案例用于展示分支生成、评估、剪枝和合并风格。
- 无案例时自动退回零样本思维树提示。

可选风格：

```bash
python -X utf8 思维树提示/scripts/render_tree_of_thought_prompt.py input.json --style structured
python -X utf8 思维树提示/scripts/render_tree_of_thought_prompt.py input.json --style expert-panel
python -X utf8 思维树提示/scripts/render_tree_of_thought_prompt.py input.json --style compact
```

## 如何选择技术

| 用户需求 | 推荐技术 |
|---|---|
| 只知道任务和输出格式 | 零样本提示 |
| 想让模型模仿几个输入输出样例 | 少样本提示 |
| 没有案例，但任务需要推理 | 零样本思维链 |
| 有同类问题的推理过程和答案 | 少样本思维链 |
| 复杂问题需要先拆小再逐个解决 | 最少到最多提示 |
| 复杂细节太多，需要先抽象原则 | 后退提示 |
| 需要比较多个路径、方案或专家视角 | 思维树提示 |

## 贡献建议

欢迎贡献：

- 新的提示工程技术 Skill。
- 更好的案例格式。
- 更稳健的输出模板。
- 不同领域的 Prompt 示例。
- 英文版 README 或双语模板。

请保持一个原则：**Skill 应该帮助用户生成更好的提示词，而不是替用户隐藏复杂流程或制造不可解释的自动化。**
