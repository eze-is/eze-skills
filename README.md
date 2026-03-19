# eze-skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一泽Eze 的 Claude Code Skills 公开合集。把日常高频用到的能力封装成 skill，让 Claude Code 开箱即用。

## Install

```bash
# 通过 Claude Code 插件市场安装
/plugin marketplace add eze-is/eze-skills

# 安装单个 skill
/plugin install web-access@eze-skills
/plugin install daily-news@eze-skills
```

或手动 clone：

```bash
git clone https://github.com/eze-is/eze-skills.git
cp -R eze-skills/web-access ~/.claude/skills/
cp -R eze-skills/daily-news ~/.claude/skills/
```

---

## Skills

| Skill | 简介 | 触发方式 |
|-------|------|---------|
| [web-access](./web-access) | v2.2 — CDP Proxy 直连用户 Chrome，WebSocket 直连 + 真实鼠标点击 + 文件上传 | 自动触发 |
| [web-access-v1](./web-access-v1) | v1 — 基于 agent-browser 的独立 Chrome 实例方案（稳定备份） | 自动触发 |
| [daily-news](./daily-news) | 每日资讯日报生成器，支持自定义信源 | 自动触发 |

---

## web-access (v2)

以**「像人一样思考，高效完成任务」**为核心理念，补全 Claude Code 的联网操作链路。v2.2 新增 WebSocket 直连、真实鼠标点击、文件上传能力。

联网工具按场景选择（非固定优先级）：

1. **WebSearch** — 搜索摘要或发现信息来源
2. **WebFetch** — URL 已知，定向提取页面信息（内置小模型处理）
3. **curl** — 需要原始 HTML 源码（meta、JSON-LD 等结构化字段）
4. **Jina** — 可选预处理层，网页转 Markdown，节省 token
5. **CDP Proxy** — 需要登录态、交互操作、或反爬严格的平台

v2.2 新增：
- **WebSocket 直连** — 去掉 HTTP `/json/version` 中间层，兼容 `chrome://inspect` 方式开启调试
- **`/clickAt`** — CDP `Input.dispatchMouseEvent` 真实鼠标点击，能触发文件对话框
- **`/setFiles`** — `DOM.setFileInputFiles` 直接设置文件路径，绕过文件对话框上传
- **站点经验积累** — 按域名存储操作经验，跨 session 复用

核心优势：
- **Token 消耗降至 1/5~1/8**（curl HTTP API vs agent-browser CLI）
- **速度最快**（直连 Chrome，无中间层）
- **并发安全**（多 agent 共享一个 proxy，tab 级别隔离，无竞态）
- **零额外依赖**（Node.js 22+ 即可，无需 npm install）
- **天然登录态**（用户日常 Chrome，无需重复登录）

```bash
bash ~/.claude/skills/web-access/scripts/check-deps.sh
```

## web-access-v1（稳定备份）

基于 [agent-browser](https://www.npmjs.com/package/agent-browser) 的方案，启动独立 Chrome 实例，通过 accessibility tree 交互。功能完整，已稳定使用。如果 v2 不适合你的场景，可以使用此版本。

主要差异：独立 Chrome profile（登录态持久化但与日常浏览器分离）、依赖 agent-browser npm 包。

---

## daily-news

三阶段工作流：**获取元数据 → 生成摘要 → 输出日报**。支持自定义信源，适合需要每日信息聚合的场景。

工作区结构：

```
<workspace>/
├── profile.yaml      # 用户画像（关注什么）
├── settings.yaml     # 日报设置
├── methods/          # 信源获取方法
├── data/news.db      # SQLite 数据库
└── output/           # 生成的日报
```

---

> Synced from [eze-skills-private](https://github.com/eze-is/eze-skills-private).
