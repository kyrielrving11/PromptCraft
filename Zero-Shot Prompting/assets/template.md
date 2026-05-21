# 零样本提示案例

## 生成 Prompt 的原则

1. 角色扮演，在提示开头明确模型的角色和任务意图。

   示例：

   ```
   你是一名专业内容摘要员，负责将文章内容提炼为关键要点。
   ```

2. 使用指令，将任务目标放在提示前部，并使用 `###`、三引号 `"""` 或代码块分隔指令和上下文。

   差例：

   ```
   Summarize the text below as a bullet point list of the most important points.

   {text input here}
   ```

   优例：

   ```
   Summarize the text below as a bullet point list of the most important points.

   Text: """
   {text input here}
   """
   ```

3. 具体且描述性，明确背景、目标、长度、格式、语言、风格和禁止项。

   差例：

   ```
   Write a poem about OpenAI.
   ```

   优例：

   ```
   Write a short inspiring poem about OpenAI, focusing on the recent DALL-E product launch in the style of a {famous poet}.
   ```

4. 减少模糊或不精确表述，指定长度、结构或风格，而非只写“简短”“详细”“专业”。

   差例：

   ```
   The description for this product should be fairly short, a few sentences only, and not too much more.
   ```

   优例：

   ```
   Use a 3 to 5 sentence paragraph to describe this product.
   ```

5. 说明该做什么，而不仅仅是不做什么。禁止项应和替代行为一起出现。

   差例：

   ```
   The following is a conversation between an Agent and a Customer. DO NOT ASK USERNAME OR PASSWORD.

   Customer: I can’t log in to my account.
   Agent:
   ```

   优例：

   ```
   The following is a conversation between an Agent and a Customer. The agent will diagnose the problem and suggest a solution. If identity verification is needed, refer the user to the help center instead of asking for username or password.

   Customer: I can’t log in to my account.
   Agent:
   ```

6. 使用“示例输出格式”表达结构要求。零样本提示可以给格式骨架，但不要提供任务级输入/输出示例。

   差例：

   ```
   Extract the entities mentioned in the text below.

   Text: {text}
   ```

   优例：

   ```
   Extract the important entities mentioned in the text below.

   Desired format:
   Company names: <comma_separated_list_of_company_names>
   People names: <comma_separated_list_of_people_names>
   Specific topics: <comma_separated_list_of_specific_topics>
   General themes: <comma_separated_list_of_general_themes>

   Text: """
   {text}
   """
   ```

7. 代码生成任务要指明语言、函数名、输入输出、依赖限制和代码块格式。

   差例：

   ```
   # Write a simple python function that converts miles to kilometers
   ```

   优例：

   ````
   Write a Python function named `miles_to_km` that accepts `miles` and returns kilometers.
   Return only a Python code block.

   ```python
   def miles_to_km(miles):
       ...
   ```
   ````

## 与少样本提示的区别

- 零样本提示不依赖用户提供的输入/输出示例。
- 零样本提示可以写“输出格式骨架”，但不要展示完整输入到输出的映射。
- 如果用户已经提供 1~5 个输入/输出示例，应优先使用少样本提示。

## Prompt 模板

<!-- PROMPT_TEMPLATE_START -->
```markdown
你是一名{角色}，负责{任务职责}。请严格按照以下要求生成输出：

### 任务
{明确的任务说明}

### 输出要求
{格式、字段、数量、语言、风格、禁止项}

### 示例输出格式
{可选：只展示格式骨架，不展示任务级输入/输出示例}

### 待处理内容
"""
{用户输入的文本}
"""
```
<!-- PROMPT_TEMPLATE_END -->

## 逐步生成方法

1. 读取任务描述和用户要求。
2. 提炼适合的角色。
3. 在开头写明任务指令。
4. 明确输出格式、长度、风格、语言和禁止项。
5. 使用三引号或代码块分隔待处理内容。
6. 对代码任务添加语言、函数签名或代码块要求。
7. 输出完整 Prompt。

## 常见 Gotchas

- 模型可能顺序错乱，需明确输出顺序。
- 模型可能添加无关解释，应指明仅输出目标结果。
- 格式骨架不是少样本示例，不要把零样本提示写成输入/输出配对。
- 对代码任务，忘记指定语言或代码块格式会导致输出不稳定。
