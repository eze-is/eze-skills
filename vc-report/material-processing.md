# 素材处理

将用户提供的素材（链接、关键词、笔记）转化为结构化的调研详情文件。

## 输入入口

### 对话直接给（主路径）

用户在对话中直接提供素材，AI 即时处理：

**A. 链接**
```
用户："帮我看下这个 https://finance.yahoo.com/news/traini-..."
```
1. 遵循 web-access skill 抓取页面内容
2. 按 `references/prompts/process-material.md` + profile.yaml 的字段规范结构化
3. 写入 `reports/当前周/research/topic.md`
4. 展示摘要供用户确认/补充

**B. 关键词**
```
用户："帮我查一下 XX 公司最近的数据"
```
1. 遵循 web-access skill 搜索相关信息
2. 筛选有价值的来源，逐个抓取
3. 综合多源信息，按 profile 字段结构化
4. 写入 `reports/当前周/research/topic.md`
5. 展示调研结果，标注信息来源

**C. 笔记**
```
用户："今天跟 XX 创始人聊了，要点是..."
```
1. 按 profile.yaml 的字段规范结构化（如按产品/模型/运营/融资拆分）
2. 写入 `reports/当前周/research/topic.md`
3. 展示结构化结果供用户确认

### inbox 批量给（补充路径）

用户提前把素材放到 `inbox/` 目录，然后告诉 AI "处理一下 inbox"。

**inbox.md**：用户在这里粘贴链接和关键词，每行一条。格式自由：
```markdown
https://finance.yahoo.com/news/traini-...
https://arxiv.org/pdf/2001.08361
查一下 XX 公司最近的 DAU 数据
某篇论文，跟某个技术方向相关
```

**其他 .md 文件**：用户直接放进 inbox 的笔记文件，当作"笔记"类型处理。

**处理流程**：
1. 读取 `inbox/inbox.md`，逐行判断类型（URL → 链接模式，其他 → 关键词模式）
2. 读取 inbox/ 中其他 .md 文件 → 笔记模式
3. 逐条处理，写入 `reports/当前周/research/`
4. 处理完成后清空 inbox.md 对应行，移动已处理文件到 `inbox/_processed/`

## research 文件格式

每个话题一个 .md 文件，文件名为话题的简短英文标识（如 `traini.md`、`chai-data.md`）。

```markdown
# {话题名称}

> 来源：{link/search/note} | {日期}
> URL：{如有}

## {板块1}（按 profile 字段规范）
- 要点1
- 要点2
- ...

## {板块2}
- ...

## 关键数据
- {数据指标}[^1]
- {数据指标}[^2]

## AI 摘要
{2-3 句话的压缩摘要，供周报直接引用或改写}

---
[^1]: https://xxx.com — 来源描述
[^2]: https://yyy.com — 来源描述
```

**脚注引用**：关键数据点必须用 `[^N]` 标注来源 URL，文末集中列出脚注。让每个数据都可溯源。

**文件中的 "AI 摘要" 段**是关键：它是调研详情到周报之间的桥梁。用户审阅时可以看到完整详情，同时也能快速看到 AI 打算怎么压缩。

## 合并逻辑

同一话题多次输入时（如先有笔记，后有链接补充）：
- 如果 `reports/当前周/research/` 已存在同话题文件 → 追加/合并内容，而非覆盖
- 更新 AI 摘要
- 标注信息来源的追加时间

## 并行调研

当用户要求同时调研多个方向时，派出子 Agent 并行处理：
- 每个子 Agent 负责一个独立话题
- prompt 中必须写：`必须加载 web-access skill 并遵循指引`
- 用"获取"而非"搜索"描述任务，让子 Agent 自主选择工具
- 每个子 Agent 的结果汇总后分别写入对应的 research 文件

## 参考

- 素材结构化 prompt：`references/prompts/process-material.md`
