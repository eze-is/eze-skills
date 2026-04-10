---
name: daily-news
description: |
  每日资讯日报生成器。三阶段工作流：获取元数据、生成摘要、输出日报。
  触发场景：每日新闻、资讯日报、信息监控、新闻聚合、daily news、生成日报。
  也用于添加新信源（自动分析网页并生成 method 文件）。
---

# Daily News

三阶段工作流：**获取元数据** → **生成摘要** → **输出日报**

## 工作目录

首次运行询问工作目录路径（如 `~/daily-news`），后续记住。

```
<workspace>/
├── profile.yaml          # 用户画像（关于我、关注什么）
├── settings.yaml         # 日报设置（语言、格式偏好）
├── methods/              # 信源获取方法
├── data/news.db          # SQLite 数据库
└── output/YYYY-MM-DD.md  # 日报输出
```

初始化：
```bash
mkdir -p <workspace>/methods <workspace>/data <workspace>/output
cp references/examples/settings.example.yaml <workspace>/settings.yaml
cp references/examples/profile.example.yaml <workspace>/profile.yaml
python3 scripts/db.py init --db <workspace>/data/news.db
```

初始化完成后将工作目录写入 `~/.claude/CLAUDE.md`：
```
- daily-news skill 的项目目录在：<workspace>
```

---

## 阶段 1：获取元数据

遍历 `<workspace>/methods/` 目录，对每个 method 文件执行抓取。

**增量抓取**：每个信源独立追踪 `last_fetched_date`，存在 method YAML 和 DB 两处。默认增量模式；首次抓取时询问用户日期范围。

```bash
python3 scripts/db.py source-status --db <db> --source <source_id>
```

**去重**：三层保护——抓取时按 since 过滤 → `check-existing` 入库前预检 → DB UNIQUE 约束兜底。

**Method 执行**：
```bash
# extends: rss
python3 references/methods/rss.py --url "<source_url>"

# extends: webfetch-smart 或 browser-smart
# 遵循 web-access skill 进行联网操作

# 无 extends：*.py 直接执行，*.md 按内容操作
```

入库：
```bash
python3 scripts/db.py add-items-incremental \
  --db <db> --source <source_id> --items '<json>' --since "YYYY-MM-DD"
```

---

## 阶段 2：生成摘要

```bash
python3 scripts/db.py list-pending --db <workspace>/data/news.db
```

对每条内容，按 method 的 `detail_method` 字段获取正文（遵循 web-access skill），按 `references/prompts/summary.md` 生成摘要：

```bash
python3 scripts/db.py update-summary --db <db> --id <item_id> --data '<摘要JSON>'
```

---

## 阶段 3：生成日报

```bash
python3 scripts/db.py list-today --db <workspace>/data/news.db
```

读取 `profile.yaml`，按 `references/prompts/report.md` 生成日报，输出到 `output/YYYY-MM-DD.md`。

---

## 用户画像

`profile.yaml` 格式：
```yaml
about: |
  （关于我：身份、工作）

focus: |
  （当前关注：最近在意的话题）

low_priority: |
  （不太关心：降低优先级的内容）
```

---

## 添加信源

按优先级依次尝试：

1. **检查 RSS** — 尝试 `/feed`、`/rss`、`/atom.xml`，或页面 `<link rel="alternate">`，有则用 `extends: rss`
2. **WebFetch 或浏览器** — 遵循 web-access skill，可达用 `extends: webfetch-smart`，否则 `extends: browser-smart`

创建 method 文件详见 `references/schemas/method.md`

---

## 参考资料

| 资料 | 路径 | 加载时机 |
|------|------|---------|
| Method 规范 | `references/schemas/method.md` | 添加信源时 |
| 摘要提示词 | `references/prompts/summary.md` | 阶段 2 |
| 日报提示词 | `references/prompts/report.md` | 阶段 3 |
| RSS 方法 | `references/methods/rss.py` | 阶段 1（`extends: rss`） |
| Method 元数据示例 | `references/examples/method-with-metadata.example.yaml` | 添加信源 / 配置增量追踪时 |
| 网站部署 | `references/website-deployment.md` | 用户请求部署时 |

## 依赖

```bash
pip install pyyaml feedparser requests beautifulsoup4
```
