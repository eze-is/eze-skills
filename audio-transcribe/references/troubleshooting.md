# 踩坑记录

## ASR 相关

| 问题 | 原因 | 正确做法 |
|------|------|---------|
| ASR 任务一直 RUNNING 不返回结果 | SDK 默认 API 端点可能不正确 | 显式设置 `dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'` |
| ASR 提交后行为异常 | `language` 参数在 filetrans 模型上可能不兼容 | 不传 `language` 参数，让模型自动识别语言 |
| HTTP POST 调用报 `AccessDenied` | 必须用 SDK | 用 DashScope Python SDK（`pip install dashscope`），不能直接 HTTP 调用 |
| 免费配额报 `Throttling.AllocationQuota` | 配额用完 | 确认账号已开通付费，或换 key |
| 时间戳单位混淆 | `begin_time` 单位是**毫秒** | 除以 1000 得秒 |
| 多段文件拼接时间错乱 | 直接拼接不考虑录制间隔 | 用文件名中的时间戳计算偏移 |

### 模型名速查

| 模型 | 用途 | 注意 |
|------|------|------|
| `qwen3-asr-flash-filetrans` | 长音频 async | SDK 用 `QwenTranscription`，参数 `file_url`（单数），结果 `output.result.transcription_url`（单数） |
| `qwen3-asr-flash` | <5min sync | 向 async API 提交会报「url error」（不是 URL 问题，是模型不支持该 API） |
| `qwen-asr-flash` / `qwen-audio-asr` | ❌ 废弃 | 报 `Model not exist` |
| `paraformer-v2`（旧版） | 旧 API | 用不同的 `Transcription` 类，`file_urls` 复数，`results` 复数，与 filetrans 完全不兼容 |

## pyannote 相关

| 问题 | 原因 | 正确做法 |
|------|------|---------|
| MP3 输入报采样数不匹配 | MP3 帧边界问题 | 脚本已内置自动转 WAV |
| `use_auth_token` 报错 | pyannote 4.x 改 API | 用 `token=`，不是 `use_auth_token=` |
| 返回值没有 `itertracks` | pyannote 4.x 改返回类型 | 返回 `DiarizeOutput`，取 `.speaker_diarization` 属性才是 Annotation |
| 首次运行报 403 | 未接受模型协议 | 登录 HF 接受协议（见 SKILL.md） |

## 上传相关

| 问题 | 原因 | 正确做法 |
|------|------|---------|
| litterbox 上传超时 | 文件太大 | 先标准化压缩（30 分钟 WAV → ~5MB MP3） |
| ASR 拿不到文件 | URL 已过期（1 小时） | 上传后尽快提交 ASR 任务 |
