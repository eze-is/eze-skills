# eze-skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一泽Eze 的 Claude Code Skills 公开合集。把日常高频用到的能力封装成 skill，让 Claude Code 开箱即用。

## Install

```bash
# 安装 web-access（最新版，独立仓库）
git clone https://github.com/eze-is/web-access.git ~/.claude/skills/web-access

# 安装 daily-news
git clone https://github.com/eze-is/eze-skills.git
cp -R eze-skills/daily-news ~/.claude/skills/
```

---

## Skills

| Skill | 简介 | 触发方式 |
|-------|------|---------|
| [web-access](https://github.com/eze-is/web-access) ↗ | v2+ — CDP Proxy 直连用户 Chrome，完整联网策略。**已迁移到独立仓库** | 自动触发 |
| [web-access-v1](./web-access-v1) | v1 — 基于 agent-browser 的独立 Chrome 实例方案（历史存档） | 自动触发 |
| [daily-news](./daily-news) | 每日资讯日报生成器，支持自定义信源 | 自动触发 |
| [vc-report](./vc-report) | VC 投资人调研周报/月报助手，profile-driven | "周报"、"调研" |

---

## web-access (v2+)

> **最新版已迁移到独立仓库：[eze-is/web-access](https://github.com/eze-is/web-access)**
>
> 本仓库不再同步 web-access 新版本，请前往独立仓库获取。

## web-access-v1（历史存档）

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

## vc-report

VC 投资人调研周报/月报助手。把零散的调研素材（链接、关键词、笔记）变成结构化的周报/月报。

核心特性：

- **Profile-driven**：先学习用户的报告风格，再按其习惯输出
- **两阶段调研**：子 Agent 客观探索（不带偏见）→ 主 Agent 认知碰撞（加载 worldview）
- **worldview.md**：持续演化的认知框架，每次调研后审视更新
- **程序化 prompt 组装**：`build-prompt.py` 根据 stage 自动隔离上下文，避免信息泄露
- **脚注引用**：关键数据标注来源 URL，可溯源
- **依赖 web-access skill** 做联网调研

工作区结构：

```
<workspace>/
├── profile.yaml          # 用户画像 + 报告风格 + 调研偏好
├── worldview.md          # 持续演化的认知框架
├── notes.md              # 调研脉络（事实层）
├── inbox/                # 素材投递入口
└── reports/              # 每期报告 = 一个子项目
    └── 2026-W15/
        ├── research/     # 调研详情（子 Agent 写入）
        └── output.md     # 最终周报
```

---

> Synced from [eze-skills-private](https://github.com/eze-is/eze-skills-private).
