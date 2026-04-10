# 报告生成 Prompt

从本周/本月的调研详情文件汇总生成结构化报告。

## 输入

- `reports/WNN/research/` 目录下的所有 .md 文件（调研详情）
- `profile.yaml`（报告结构、风格、调研偏好）
- `worldview.md`（认知框架，用于交叉判断）
- `notes.md`（调研脉络和判断，如有）

## 生成规则

### 内容组织

1. **按 profile.structure 排列板块**，保持用户习惯的顺序
2. **自动归类**：
   - 来源为 note 且涉及面对面交流 → Meeting
   - 来源为 link/search → Desktop research
   - 归类不确定时，按内容性质判断而非死板规则
3. **同话题合并**：同一公司/产品的多条素材合并为一个条目
4. **相关话题可聚合呈现**：如果多个话题属于同一趋势，可以在一个小标题下一起写，再分别展开
5. **参考链接汇总**：从所有 research 文件中提取参考链接，去重后汇总到 Intriguing references
6. **Next on 建议**：从 notes.md 的待办事项 + research 文件中识别的未完成线索生成

### 压缩策略

- **Meeting 条目**：保留 profile 定义的 subsections 结构，每个 subsection 压缩到 2-4 个核心要点
- **Desktop research 条目**：使用 research 文件中的 AI 摘要为基础，补充关键数据
- **保留个人判断**：用户或 notes.md / worldview.md 中的主观判断必须保留（这是报告的独特价值）
- **保留关键数据**：精确的数字指标（DAU、ARR、留存率等）不能在压缩中丢失
- **遵循 research_preferences**：按 profile.yaml 的 `research_preferences` 控制呈现角度。数据是佐证，不是主体；关注战略含义而非技术细节

### 脚注引用

周报中的关键数据点必须用脚注标注来源 URL：

```markdown
CLI 工具比 MCP 便宜 10-32x[^1]，XX 公司 DAU 涨到了 160w[^2]

---
[^1]: https://example.com/benchmark — benchmark 文章
[^2]: https://example.com/source — 数据来源
```

脚注从 research 文件的脚注中继承。如果 research 文件中标注了 `[unverified]`，周报中不引用该数据点，或标注不确定性。

### 风格遵循

- 按 profile.report_style.tone 中的风格要求输出
- 参考 profile.report_style.sample_snippets 中的表达方式
- 保持用户习惯的中英文混用模式
- **Desktop research 每条控制在 2-5 行要点**，不写长段分析。个人判断用括号自然穿插

## 输出格式

按 profile.yaml 的 structure 动态生成。不同用户的报告结构可能完全不同。

## URL 校验

生成完成后，对所有脚注和 Intriguing references 中的 URL 做一次有效性检查：
- 遵循 web-access skill，WebFetch 检查可访问性
- 无法访问 → 标注 `[链接失效]` 或替换
- 微信公众号链接（mp.weixin.qq.com）跳过校验（通常有效但不可被 WebFetch 抓取）

## 月报特殊处理

月报不是四份周报的拼接，而是：
- 按话题/赛道聚合，而非按周聚合
- 侧重趋势变化（某赛道本月的整体走向）
- 重点项目的进展时间线
- 本月的关键判断演变（从 notes.md + worldview.md 提取）
