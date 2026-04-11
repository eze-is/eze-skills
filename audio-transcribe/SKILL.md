---
name: audio-transcribe
description: |
  录音文件转录能力。将音频文件转为结构化文本（带时间戳 + 说话人标识）。
  这是一个场景能力 skill，类似 web-access——只负责"把声音变成文字"，不决定文字用来做什么。
  触发场景：用户提供录音文件、要求转录音频、处理语音文件。
metadata:
  author: 一泽Eze
  version: "1.0.0"
  created: 2026-04-10
  depends:
    - ffmpeg
    - dashscope (pip)
    - pyannote.audio (pip, 可选)
---

# 录音转录能力

## 定位

**场景能力 skill**，对标 web-access 的角色。

- web-access：给你联网能力（搜索/抓取/浏览），不管你拿内容做什么
- audio-transcribe：给你录音转文字能力（转录/说话人分离），不管你拿文字做什么

转录产出是**原料**，不是终态。调用方决定这些文字变成会议纪要、周报素材、播客摘要还是别的什么。

## 前置检查

使用前先检查环境依赖：

```bash
bash ~/.claude/skills/audio-transcribe/scripts/check-deps.sh
```

未通过时引导用户安装：
- **ffmpeg**：音频标准化必需。`brew install ffmpeg`
- **dashscope**：阿里云 ASR 服务。`pip install dashscope`
- **DASHSCOPE_API_KEY**：阿里云百炼 API Key
- **HF_TOKEN**（首次下载 pyannote 模型时需要）：HuggingFace token
- **pyannote.audio**（可选）：说话人分离。`pip install pyannote.audio`，需接受模型协议

**密钥持久化**：将 API Key 存入 `~/.claude/.env`，脚本自动加载，跨会话持久生效：
```
DASHSCOPE_API_KEY=sk-xxx
HF_TOKEN=hf_xxx
```
优先级：环境变量 > `~/.claude/.env`。pyannote 模型缓存到本地后，后续不再需要 HF_TOKEN。

## 工作流

```
原始录音（.wav/.m4a/.mp3/.aac/...各种格式和采样率）
    ↓  Stage 1: 标准化
标准化音频（16kHz mono MP3，ASR 最优格式）
    → 存放：/tmp/audio-transcribe/{batch-id}/normalized/
    ↓  Stage 2: 上传 + ASR 转录
原始转录句子（字级时间戳）
    ↓  Stage 3: 说话人分离
带说话人标识的句子
    ↓  Stage 4: 格式化输出
结构化转录文本（.transcript.md + .transcript.json）
    → 存放：调用方指定的 --output-dir，或源文件同目录
```

### 说话人分离的重要性

**说话人分离是默认行为，不是可选项。** 多人对话录音中，"谁说了什么"是信息的核心维度——没有说话人标识的转录文本会丢失归属关系，下游加工（会议纪要、调研提炼）的质量会大幅下降。

- **默认开启**：除非用户明确指定 `--no-diarization`（如独白、播客等单人场景），转录时必须执行说话人分离
- **前置检查**：转录前确认 HF_TOKEN 已配置（`~/.claude/.env` 或环境变量），pyannote 模型已缓存。缺失时应提醒用户，而非静默跳过
- **补跑机制**：如果转录已完成但缺少说话人分离（如首次配置 HF_TOKEN 之前的转录），使用 `--diarize-only` 补跑——复用已有的 ASR 结果（`.transcript.json`），只跑 pyannote 说话人分离并更新输出，避免重复消耗 ASR 资源

### 产物存放规则

| 产物 | 性质 | 存放位置 |
|------|------|---------|
| 标准化音频 | 纯中间产物，转录完即废弃 | `/tmp/audio-transcribe/{batch-id}/` |
| `.transcript.md` | 可读的转录文本，调用方的输入 | `--output-dir` 或源文件同目录 |
| `.transcript.json` | 原始数据（字级时间戳等），溯源用 | 同上 |

## 脚本 API

以下命令中 `transcribe.py` 均指 `python3 ~/.claude/skills/audio-transcribe/scripts/transcribe.py`。

### 基本用法

```bash
# 单文件转录
transcribe.py meeting.m4a

# 批量转录（每个文件独立处理）
transcribe.py file1.m4a file2.wav file3.mp3

# 指定输出目录
transcribe.py *.m4a --output-dir /path/to/transcripts/

# 同一场会议的多段录音（合并时间轴为一份转录）
transcribe.py seg1.wav seg2.wav seg3.wav --merge

# 跳过说话人分离
transcribe.py audio.mp3 --no-diarization

# 补跑说话人分离（复用已有 ASR 转录，只跑 diarization）
transcribe.py audio.m4a --diarize-only --output-dir /path/to/transcripts/
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `files` | 音频文件路径（支持多个） | 必填 |
| `--output-dir` | 转录文件输出目录 | 源文件同目录 |
| `--diarize-only` | 仅补跑说话人分离（需已有 .transcript.json） | 否 |
| `--merge` | 多文件视为同一场会议，合并时间轴输出一份转录 | 否（每文件独立） |
| `--no-diarization` | 跳过说话人分离（独白、播客等不需要） | 否 |
| `--hf-token` | HuggingFace token（也可用 HF_TOKEN 环境变量） | 环境变量 |

### 输出文件

每个音频文件（或 merge 模式下的一组文件）产出两个文件：

**`{name}.transcript.md`** — 可读转录文本：
```
# 转录：{原始文件名}

> 时长：42:15 | 说话人：3 | 转录时间：2026-04-10

[00:00] SPEAKER_00: 开场白...
[00:05] SPEAKER_01: 回应...
[01:23] SPEAKER_00: 继续讨论...
```

**`{name}.transcript.json`** — 结构化原始数据：
```json
{
  "source_files": ["meeting.m4a"],
  "duration_seconds": 2535,
  "speakers": ["SPEAKER_00", "SPEAKER_01", "SPEAKER_02"],
  "sentences": [
    {
      "begin_time": 0,
      "end_time": 4500,
      "text": "开场白...",
      "speaker": "SPEAKER_00",
      "emotion": "neutral",
      "words": [...]
    }
  ]
}
```

## 调用方集成模式

### 模式 A：子 Agent 批量转录

适合一次性处理多个录音（如 vc-report 收到 10+ 份路演录音）：

```
主 Agent
  ├─ 子 Agent 1: transcribe.py file1.m4a --output-dir /tmp/...
  ├─ 子 Agent 2: transcribe.py file2.m4a --output-dir /tmp/...
  └─ ...
  主 Agent 读取所有 .transcript.md，按自己的格式要求加工
```

每个子 Agent 独立处理一个文件，并行不冲突。

### 模式 B：直接调用

适合单文件或少量文件：

```
Agent 直接调用 transcribe.py → 读取 .transcript.md → 加工
```

### 调用方的职责

audio-transcribe 产出的是**带时间戳和说话人的原始转录文本**。调用方负责：
- 决定转录文本的**用途**（会议纪要？周报素材？日志？）
- 决定**摘要格式**（投资洞察？行动项？关键决策？）
- 决定**最终产出位置**（项目目录下的哪里）
- 将说话人 ID（SPEAKER_00）**映射为真实身份**（如果需要）

## 技术细节

### 音频标准化参数

```bash
ffmpeg -i input.wav -ar 16000 -ac 1 -b:a 24k output.mp3 -y
```

- `-ar 16000`：16kHz，ASR 标准采样率（人声频率在 8kHz 以下，无损失）
- `-ac 1`：单声道（立体声对 ASR 无意义）
- `-b:a 24k`：24kbps，语音清晰，体积极小（30 分钟约 5MB）

### ASR 服务

使用 `qwen3-asr-flash-filetrans`（阿里云百炼），异步长音频转写，最长支持 12 小时。

转录流程需要 ASR 服务端可访问的音频 URL。使用 DashScope Files API 上传到阿里云 OSS，获取签名 URL 供 ASR 读取。

### 说话人分离

使用 pyannote/speaker-diarization-3.1（本地模型），与 ASR 结果按时间戳对齐。

首次使用需在 HuggingFace 接受模型协议：
- https://huggingface.co/pyannote/speaker-diarization-3.1
- https://huggingface.co/pyannote/segmentation-3.0

模型下载后本地缓存，后续完全离线。Apple MPS 加速可用。

### 多段文件合并

`--merge` 模式下，根据文件名中的时间戳计算各段的时间偏移，合并为统一时间轴。当前支持 DJI Mic 3 的文件名格式（`TX02_MIC001_20260319_090113.wav`），其他格式按文件顺序拼接。

## References 索引

| 文件 | 何时加载 |
|------|---------|
| `references/troubleshooting.md` | 遇到 ASR/pyannote 报错时 |
