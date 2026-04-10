# 风格学习

从用户的历史周报样本中提取报告风格，生成 `profile.yaml`。

## 触发时机

- 首次使用（profile.yaml 不存在）
- 用户丢入新的样本周报
- 用户说"学习这个风格"/"更新风格"

## 流程

1. 读取 `samples/` 中的所有周报文件
2. 按 `references/prompts/analyze-style.md` 分析，提取：
   - **结构模板**：报告有哪些板块、什么顺序、层级关系
   - **字段规范**：每个板块下通常包含哪些字段（如 Meeting 下分产品/模型/运营/融资）
   - **语言风格**：中英混用程度、是否带主观判断、括号吐槽、数据引用习惯
   - **信息粒度**：数据精确度偏好（百分比/数量级）、定性 vs 定量
   - **关注领域**：从样本中提取用户实际在跟踪的赛道和公司
3. 生成 `profile.yaml`，向用户展示提取结果
4. 用户确认或修正 → 更新 profile.yaml

## profile.yaml 结构

```yaml
# 基本信息
name: ""
role: ""                          # 如 "VC 投资人"
firm: ""                          # 如 "某基金"

# 关注领域（从样本中提取 + 用户补充）
domain: ""                        # 如 "AI 软件"
focus_areas: []                   # 如 ["AI 社交", "AI 游戏", "宠物科技"]

# 报告风格（从样本中学习得到）
report_style:
  # 结构模板 — 报告的板块和顺序
  structure:
    - section: "Meeting"
      description: "本周会议记录"
      subsections: []             # 如 ["产品规划", "模型构建", "运营情况", "团队和融资"]
    - section: "Desktop research"
      description: "桌面调研"
    - section: "Next on"
      description: "下周计划"
    - section: "Intriguing references"
      description: "参考链接"

  # 语言风格
  tone: []
  # 示例：
  # - "中英文混用，专业术语用英文"
  # - "带个人判断和情绪（如括号吐槽）"
  # - "数据尽量精确"

  # 信息粒度
  detail_level:
    meeting: ""                   # 如 "按子模块详细展开，每个模块 3-5 个要点"
    desktop_research: ""          # 如 "简要总结 + 关键数据点"
    references: ""                # 如 "标题 + URL，一行一个"

  # 风格参考片段（从样本中摘取的典型表达）
  sample_snippets: []

# 输出格式
output_format: "markdown"
```

## 风格更新

用户修改了生成的报告时触发：

1. 对比修改前后的差异
2. 判断是通用偏好还是本次特定
3. 通用偏好 → 确认 → 更新 profile.yaml 对应字段
4. 本次特定 → 记录到 notes.md

## 参考

- 风格提取 prompt：`references/prompts/analyze-style.md`
- profile 示例：`references/examples/profile.example.yaml`
