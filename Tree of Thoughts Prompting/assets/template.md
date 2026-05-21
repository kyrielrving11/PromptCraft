# 思维树提示模板

## 论文机制提炼

Tree of Thoughts 将问题求解看成搜索树：

1. Thought decomposition：定义中间思路的粒度。
2. Thought generation：在每个状态生成多个候选思路。
3. State evaluation：评价候选状态的进展，作为搜索启发式。
4. Search algorithm：按宽度优先、深度优先、beam search 或专家投票等方式探索、剪枝和回溯。

用于提示词生成时，不一定要真的调用外部搜索程序；可以把这些机制压缩成一个结构化 Prompt，让模型在一次回复中模拟有限深度、有限分支的树搜索。

## 生成 Prompt 的原则

1. 明确当前任务的 `thought` 粒度。
2. 明确每轮生成几个候选、最多几轮、每轮保留几个分支。
3. 明确评价标准和评分尺度。
4. 明确剪枝/回溯条件。
5. 明确最终选择或合并规则。
6. 明确输出格式：表格字段、最终答案位置、是否展示过程。
7. 用户提供案例时，将案例作为分支生成、评估、剪枝和合并风格参考；没有案例时按零样本思维树提示生成并说明原因。
8. 避免要求完整隐藏思维链；输出可公开的候选思路、评估摘要和结论。

## 标准结构化 ToT Prompt 模板

<!-- STRUCTURED_TEMPLATE_START -->
{ROLE}

请使用 Tree of Thoughts（思维树）方法处理任务。你的目标不是沿着单一路径直接回答，而是在有限分支和有限深度内探索多个候选思路，评价并剪枝，最后选择或综合最优路径给出答案。

### 原始任务
{TASK}

### 待处理内容
"""
{TARGET_INPUT}
"""

### 可选参考案例
{EXAMPLES_SECTION}

### 思维树配置
- Thought 粒度：{THOUGHT_UNIT}
- 搜索策略：{SEARCH_STRATEGY}
- 每轮候选数：{BRANCH_COUNT}
- 最大迭代深度：{MAX_DEPTH}
- 每轮保留分支数：{KEEP_COUNT}
评价标准：
{EVALUATION_CRITERIA}
- 决策规则：{DECISION_RULE}

### 输出要求
{OUTPUT_FORMAT}

### 约束条件
{CONSTRAINTS}

### 执行方法
1. 初始化根节点：把原始任务作为根状态。
2. 第 1 到 {MAX_DEPTH} 轮：
   - 从每个保留状态生成最多 {BRANCH_COUNT} 个候选 thought。
   - 用评价标准为每个候选打分或给出等级。
   - 剪枝明显违反约束、不可行、重复或低价值的候选。
   - 保留最多 {KEEP_COUNT} 个最有希望的状态进入下一轮。
   - 如果已经得到满足输出要求的高置信答案，可以提前停止。
3. 如果保留分支陷入死路，回溯到上一轮次优分支重新展开。
4. 最终根据决策规则选择或综合答案。
5. 输出控制：{TRACE_VISIBILITY}

### 建议输出结构
如果允许展示过程，请使用 Markdown 表格：

| 轮次 | 分支 | 候选 thought 摘要 | 评分/等级 | 保留/剪枝 | 理由 |
|---|---|---|---|---|---|

然后输出：

#### 最终选择
说明采用哪个分支或如何综合。

#### 最终答案
按用户要求的格式输出。

如果输出要求指定了严格格式，请优先满足该格式。
<!-- STRUCTURED_TEMPLATE_END -->

## 专家协作式 ToT Prompt 模板

<!-- EXPERT_PANEL_TEMPLATE_START -->
{ROLE}

请使用专家协作式 Tree of Thoughts 方法处理任务。你将模拟 {BRANCH_COUNT} 位不同视角的专家，每位专家在每轮提出一个候选 thought；随后所有候选会被评价、剪枝和合并。专家只是产生多样化分支的方式，最终必须遵守统一的评价和决策规则。

### 原始任务
{TASK}

### 待处理内容
"""
{TARGET_INPUT}
"""

### 可选参考案例
{EXAMPLES_SECTION}

### 专家角色
{EXPERT_ROLES}

### 思维树配置
- Thought 粒度：{THOUGHT_UNIT}
- 最大迭代深度：{MAX_DEPTH}
- 每轮保留分支数：{KEEP_COUNT}
评价标准：
{EVALUATION_CRITERIA}
- 决策规则：{DECISION_RULE}

### 输出要求
{OUTPUT_FORMAT}

### 约束条件
{CONSTRAINTS}

### 执行方法
1. 每位专家在当前轮次提出 1 个候选 thought，必须考虑上一轮保留分支。
2. 专家可以指出自己或其他分支的错误；发现明显错误的分支应退出或被剪枝。
3. 对所有候选按评价标准打分，保留最多 {KEEP_COUNT} 个分支。
4. 重复最多 {MAX_DEPTH} 轮；若已有高置信结论，可提前停止。
5. 最终按决策规则选择或综合答案。
6. 输出控制：{TRACE_VISIBILITY}

### 建议输出结构
使用 Markdown 表格：

| 轮次 | 专家/分支 | 候选 thought 摘要 | 对他人思路的吸收或修正 | 评分 | 状态 |
|---|---|---|---|---|---|

最后输出：

#### 合并决策
...

#### 最终答案
...
<!-- EXPERT_PANEL_TEMPLATE_END -->

## 紧凑 ToT Prompt 模板

<!-- COMPACT_TEMPLATE_START -->
{ROLE}

请用紧凑版 Tree of Thoughts 处理任务：生成 {BRANCH_COUNT} 个候选方案，按评价标准评分，保留最优 {KEEP_COUNT} 个并最多迭代 {MAX_DEPTH} 轮，最后按决策规则输出答案。不要展开冗长推理，只输出候选摘要、评分和最终答案。

### 任务
{TASK}

### 待处理内容
"""
{TARGET_INPUT}
"""

### 可选参考案例
{EXAMPLES_SECTION}

### 评价标准
{EVALUATION_CRITERIA}

### 输出要求
{OUTPUT_FORMAT}

### 约束条件
{CONSTRAINTS}

### 决策规则
{DECISION_RULE}
<!-- COMPACT_TEMPLATE_END -->

## 逐步生成方法

1. 读取任务、待处理内容、输出格式、约束和可选案例。
2. 判断任务是否需要 ToT；简单任务改用零样本或 CoT。
3. 选择模板：标准结构化、专家协作式或紧凑版。
4. 有用户案例时格式化为参考案例；没有案例时写明按零样本思维树提示生成。
5. 为任务定义合适的 thought 粒度。
6. 设置保守搜索参数：默认候选数 3、深度 3、保留 2。
7. 写清评价标准、剪枝规则和最终决策方式。
8. 输出完整 Prompt。

## 常见 Gotchas

- 只有“三个专家轮流想”不够；必须有候选评价、剪枝和最终决策。
- 候选数和深度不受限会导致输出过长。
- Thought 粒度过大，模型难以评价；过小，又没有语义价值。
- 专家角色太空泛会造成重复；应让角色覆盖不同视角，如正确性、创造性、风险、实现。
- 严格输出任务应把树搜索作为内部工作，最终只输出目标格式。
