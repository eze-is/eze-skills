# 报告生成

从子项目的 `research/` 目录汇总生成周报或月报。

## 触发

- "生成本周调研" / "出周报" / "本周汇总"
- "生成月报" / "本月汇总"

## 周报流程

1. **确定周期**：当前 ISO 周（如 2026-W15），或用户指定的周
2. **读取素材**：遍历 `reports/2026-W15/research/` 所有 .md 文件
3. **读取 profile**：加载 profile.yaml 的报告结构模板和风格
4. **按模板组织**：
   - 按 profile.structure 的板块顺序排列
   - 每条素材根据来源类型自动归类（笔记类多归 Meeting，链接/搜索类多归 Desktop research）
   - 同一项目/公司的多条素材合并
   - 从各文件的"参考链接"段提取所有 URL，汇总到 Intriguing references
   - 从各文件中识别未完成的调研线索，生成 Next on 建议
5. **压缩内容**：
   - 优先使用各 research 文件中的 "AI 摘要" 段
   - 按 profile 的 detail_level 控制信息量
   - 保留关键数据指标
   - 保留用户的个人判断（notes.md 中的 consensus 和 user 标注）
6. **输出**：写入 `reports/2026-W15/output.md`
7. **展示给用户**：用户可修改，触发风格学习

## 月报流程

1. 创建月报子项目：`reports/2026-04-monthly/`
2. 聚合当月所有周报子项目的 research 文件（`reports/2026-W14/research/` + `reports/2026-W15/research/` + ...）
3. 按 profile 模板组织，但侧重：
   - 趋势总结而非逐条罗列
   - 跨周对比（如某公司本月的数据变化）
   - 重点项目的进展汇总
4. 月报如有专属调研 → 写入 `reports/2026-04-monthly/research/`
5. 输出到 `reports/2026-04-monthly/output.md`

## 报告格式

按 profile.yaml 的 structure 字段动态生成。以下是一个示例（基于 VC 投资人的典型格式）：

```markdown
# Wrap up — 2026-W15

## Meeting
### {项目名}：{一句话定位}
- {子板块1}
  - 要点...
- {子板块2}
  - 要点...

## Desktop research
- {话题1}
  - 关键发现...
- {话题2}
  - 关键发现...

## Next on
- {下周计划1}
- {下周计划2}

## Intriguing references
- {标题} {URL}
- {标题} {URL}
```

## 脚注引用

周报中的关键数据点必须用脚注标注来源，从 research 文件的脚注中继承：

```markdown
XX 公司 DAU 涨到了 160w[^1]，CLI 工具比 MCP 便宜 10-32x[^2]

---
[^1]: https://example.com/source — 数据来源
[^2]: https://example.com/benchmark — benchmark 文章
```

Intriguing references 板块的链接不需要脚注（它本身就是链接列表）。

## URL 有效性校验

生成周报后、展示给用户前，对所有引用的 URL（脚注 + Intriguing references）做一次快速检查：
1. 遵循 web-access skill，逐个 WebFetch 检查是否可访问
2. 无法访问的 URL 标注 `[链接失效]` 或替换为可用的替代来源
3. 微信公众号链接（mp.weixin.qq.com）通常有效但不可被 WebFetch 抓取，可跳过校验

## 用户修改与反馈

用户看到生成的周报后可能会：
- "这个项目的部分太简略了，把运营数据加回来" → 从 research 文件中补充
- "Desktop research 里这条不重要，删掉" → 删除并记录偏好
- "融资信息应该放在更前面" → 更新 profile.yaml 的 subsections 顺序
- "这个表述不对" → 直接修正

每次修改都是风格学习的输入（见 profile-learning.md）。

## 参考

- 报告生成 prompt：`references/prompts/generate-report.md`
