# web-access

给 Claude Code 装上完整联网能力的 skill。

Claude Code 原本就有 WebSearch、WebFetch、Playwright MCP，但没有调度策略——不知道什么时候该用哪个，也没有激活 CDP 登录态复用这个最强能力。这个 skill 补上的正是这一层：**策略 + 解锁**。

## 能力

| 能力 | 说明 |
|------|------|
| 三层通道自动调度 | WebSearch → Jina/WebFetch → 浏览器 CDP，自主选择最轻的直达方案 |
| 浏览器 CDP 模式 | 直连用户日常 Chrome，天然携带登录态，支持动态页面、交互操作、视频截帧 |
| 并行分治 | 多目标时主 Agent 分发子 Agent 并行执行，总耗时 ≈ 单个子任务时长 |
| 图片 / 视频提取 | 从 DOM 直取媒体 URL，或对视频任意时间点截帧分析 |

## 安装

**方式一：让 Claude 自动安装**

```
帮我安装这个 skill：https://github.com/eze-is/web-access
```

**方式二：手动**

```bash
git clone https://github.com/eze-is/web-access ~/.claude/skills/web-access
```

## 前置配置（CDP 模式）

CDP 模式需要 Node.js 22+ 和 Chrome 开启远程调试：

1. Chrome 地址栏打开 `chrome://inspect/#remote-debugging`
2. 勾选 **Allow remote debugging for this browser instance**（可能需要重启）

运行环境检查：

```bash
bash ~/.claude/skills/web-access/scripts/check-deps.sh
```

## 使用

安装后直接让 Agent 执行联网任务，skill 自动接管：

- "帮我搜索 xxx 最新进展"
- "读一下这个页面：[URL]"
- "抓取小红书上关于 xxx 的评论"
- "同时调研这 5 个产品的官网，给我对比摘要"

## License

MIT · 作者：[一泽 Eze](https://github.com/eze-is)
