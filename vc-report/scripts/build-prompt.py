#!/usr/bin/env python3
"""
子 Agent prompt 组装脚本。
根据 stage 参数程序化决定注入哪些上下文，避免主 Agent 手动拼接出错。
"""

import argparse
import os
import sys
import yaml
import json
from datetime import date


def load_file(path):
    """读取文件内容，不存在则返回 None"""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return None


def load_yaml(path):
    """读取 YAML 文件，不存在则返回空 dict"""
    content = load_file(path)
    if content:
        return yaml.safe_load(content)
    return {}


def build_stage1_prompt(topic, initial_info, output_path, depth="medium"):
    """
    阶段 1：客观探索 prompt
    不注入 worldview、不注入 research_preferences
    """

    depth_guide = {
        "shallow": "调研深度偏浅，快速了解即可，不需要过度深挖。",
        "medium": "中等深度调研，需要充分发散探索。",
        "deep": "深度调研，全面探索所有可能的方向。"
    }

    prompt = f"""你是一个调研员，负责客观调研一个话题。你的任务是深入调研后把结果写入文件。

## 调研目标
{topic}

## 初始信息
{initial_info}

## 调研深度
{depth_guide.get(depth, depth_guide["medium"])}

## 调研标准

### 第一层：理解（必做）
- 这是什么？解决什么问题？
- 核心产品/技术/概念是什么？
- 用户给的信息源说了什么？

### 第二层：发散（主动探索）
- 横向：同赛道还有谁在做？路线有什么不同？
- 纵向：上下游是什么？依赖什么？服务什么场景？
- 时间线：从什么时候开始的？最近有什么变化？
- 人：创始人/核心团队是谁？背景？（如果是创业项目）

## 写入要求
- 边调研边写，append 式追加到文件
- 每完成一个探索动作就写入一个 section
- 事实详尽，关键数据精确保留
- 关键数据点必须用脚注标注来源 URL，格式：`[^N]` + 文末脚注列表
- 不做价值判断，只写事实
- 区分确认的事实和推断（推断用"可能"/"推测"标注）
- 信息来源不够可靠时标注 `[unverified]`

## 文件路径
写入：{output_path}

文件开头格式：
```
# {{话题名}}

> 调研进行中 | {date.today().isoformat()}
> 来源：{{初始信息来源描述}}

## 初始信息
...
```

调研完成后把"调研进行中"改为"调研完成"。

必须加载 web-access skill 并遵循指引。不要浅尝辄止，充分探索。"""

    return prompt


def build_stage2_prompt(workspace, topic, research_files):
    """
    阶段 2：认知碰撞 prompt
    注入 worldview + research_preferences
    """

    profile = load_yaml(os.path.join(workspace, 'profile.yaml'))
    worldview = load_file(os.path.join(workspace, 'worldview.md'))

    # 提取 research_preferences
    prefs = profile.get('research_preferences', {})
    prefs_text = ""
    if prefs:
        prefs_text = "\n## 调研偏好（来自 profile）\n"
        if prefs.get('perspective'):
            prefs_text += f"- 视角：{prefs['perspective']}\n"
        if prefs.get('focus'):
            prefs_text += "- 关注：\n"
            for f in prefs['focus']:
                prefs_text += f"  - {f}\n"
        if prefs.get('avoid'):
            prefs_text += "- 避免：\n"
            for a in prefs['avoid']:
                prefs_text += f"  - {a}\n"

    # worldview 内容
    worldview_text = ""
    if worldview:
        worldview_text = f"\n## 当前认知框架（worldview.md）\n\n{worldview}\n"

    prompt = f"""你是主分析师，负责对已完成的调研进行认知碰撞和交叉分析。

## 任务
对以下话题的调研结果进行阶段 2 分析：{topic}

## 已完成的 research 文件
{', '.join(research_files)}

请读取这些文件，然后：

### 第三层：交叉分析
- 新发现跟已有认知一致？→ 记录为验证
- 新发现跟已有认知矛盾？→ 这是最有价值的信号，标注出来
- 不同话题之间有什么关联？
- 有没有共同的底层趋势？

### 第四层：判断
- 投资视角：这意味着什么机会或风险？
- 值不值得深入跟进？
- 更新 worldview.md
{prefs_text}
{worldview_text}"""

    return prompt


def main():
    parser = argparse.ArgumentParser(description='组装子 Agent prompt')
    parser.add_argument('--stage', type=int, required=True, choices=[1, 2],
                       help='调研阶段：1=客观探索，2=认知碰撞')
    parser.add_argument('--topic', type=str, required=True,
                       help='调研话题名称')
    parser.add_argument('--initial-info', type=str, default='',
                       help='用户提供的初始信息')
    parser.add_argument('--output-path', type=str, default='',
                       help='research 文件写入路径（stage 1 必填）')
    parser.add_argument('--workspace', type=str, required=True,
                       help='工作区根目录路径')
    parser.add_argument('--depth', type=str, default='medium',
                       choices=['shallow', 'medium', 'deep'],
                       help='调研深度（stage 1 用）')
    parser.add_argument('--research-files', type=str, nargs='*', default=[],
                       help='已完成的 research 文件路径列表（stage 2 用）')

    args = parser.parse_args()

    if args.stage == 1:
        if not args.output_path:
            print("错误：stage 1 必须指定 --output-path", file=sys.stderr)
            sys.exit(1)
        prompt = build_stage1_prompt(
            topic=args.topic,
            initial_info=args.initial_info,
            output_path=args.output_path,
            depth=args.depth
        )
    elif args.stage == 2:
        prompt = build_stage2_prompt(
            workspace=args.workspace,
            topic=args.topic,
            research_files=args.research_files
        )

    print(prompt)


if __name__ == '__main__':
    main()
