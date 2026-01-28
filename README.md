# eze-skills

My Claude Code Skills collection.

## Skills

| Skill | Description | Trigger |
|-------|-------------|---------|
| [daily-news](./daily-news) | 每日资讯日报生成器。三阶段工作流：获取元数据、生成摘要、输出日报 | `/daily-news` |

## Installation

```bash
git clone https://github.com/eze-is/eze-skills.git

# Copy skills to Claude Code directory
cp -R eze-skills/daily-news ~/.claude/skills/
```

## Development

This repository is synced from [eze-skills-private](https://github.com/eze-is/eze-skills-private).

```bash
# Sync from private repo
./sync.sh
```
