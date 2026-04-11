#!/usr/bin/env python3
"""
录音转录脚本 — audio-transcribe skill 的核心工具

用法:
    python3 transcribe.py audio.m4a                          # 单文件
    python3 transcribe.py *.m4a --output-dir ./transcripts/  # 批量 + 指定输出
    python3 transcribe.py seg1.wav seg2.wav --merge           # 同一场会议多段合并
    python3 transcribe.py audio.mp3 --no-diarization          # 跳过说话人分离

环境变量:
    DASHSCOPE_API_KEY   阿里云百炼 API Key（必需）
    HF_TOKEN            HuggingFace token（说话人分离用，可选）
"""

import os
import sys
import json
import time
import uuid
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# 从 ~/.claude/.env 加载密钥（环境变量优先）
_env_file = Path.home() / ".claude" / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


# 强制 stdout 不缓冲，确保实时输出进度
def log(msg: str):
    print(msg, flush=True)


# ─── Stage 1: 音频标准化 ──────────────────────────────────────────────

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac", ".wma", ".opus", ".webm"}


def is_audio_file(path: str) -> bool:
    return Path(path).suffix.lower() in AUDIO_EXTENSIONS


def get_audio_duration(file_path: str) -> float | None:
    """用 ffprobe 获取音频时长（秒），失败返回 None"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip()) if result.returncode == 0 else None
    except (ValueError, subprocess.TimeoutExpired):
        return None


def normalize_audio(file_path: str, output_dir: Path) -> str:
    """将任意音频格式标准化为 16kHz mono MP3（ASR 最优格式）"""
    src = Path(file_path)
    dst = output_dir / f"{src.stem}.mp3"

    duration = get_audio_duration(file_path)
    duration_info = f", 原始时长 {int(duration // 60)}:{int(duration % 60):02d}" if duration else ""

    cmd = [
        "ffmpeg", "-i", str(src),
        "-ar", "16000",   # 16kHz，ASR 标准
        "-ac", "1",       # 单声道
        "-b:a", "24k",    # 24kbps，语音足够
        str(dst), "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 标准化失败: {result.stderr[:500]}")

    size_kb = dst.stat().st_size // 1024
    log(f"  标准化: {src.name} → {dst.name} ({size_kb}KB{duration_info})")
    return str(dst)


# ─── Stage 2: 上传 + ASR 转录 ─────────────────────────────────────────

def upload_for_asr(file_path: str) -> str:
    """上传音频文件，返回 ASR 可访问的 URL

    使用 DashScope Files API 上传到阿里云 OSS，确保 ASR 服务端能访问。
    """
    file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
    log(f"  上传 {Path(file_path).name} ({file_size_mb:.1f}MB)...")

    upload_result = dashscope.Files.upload(
        file_path=file_path,
        purpose="file-extract",
    )
    if upload_result.status_code != 200:
        raise RuntimeError(f"文件上传失败: {upload_result}")

    file_id = upload_result.output["uploaded_files"][0]["file_id"]
    log(f"  file_id: {file_id}")

    # 获取 OSS 签名 URL
    detail = dashscope.Files.get(file_id)
    if detail.status_code != 200:
        raise RuntimeError(f"获取文件详情失败: {detail}")

    oss_url = detail.output["url"]
    log(f"  → OSS URL 获取成功")
    return oss_url


def transcribe_asr(url: str) -> list[dict]:
    """提交 qwen3-asr-flash-filetrans 异步转录任务，返回句子列表"""
    log(f"  提交 ASR 任务...")
    task_response = QwenTranscription.async_call(
        model="qwen3-asr-flash-filetrans",
        file_url=url,
        enable_itn=False,
        enable_words=True,
    )
    if task_response.status_code != 200:
        raise RuntimeError(f"ASR 提交失败 (status {task_response.status_code}): {task_response}")

    task_id = task_response.output.task_id
    log(f"  task_id: {task_id}，等待完成...")

    start = time.time()
    result = QwenTranscription.wait(task=task_id)
    if result.output.get("task_status") in ("FAILED", "failed"):
        raise RuntimeError(f"ASR 任务失败: {result.output}")

    transcript_url = result.output["result"]["transcription_url"]
    data = requests.get(transcript_url, timeout=60).json()
    sentences = data["transcripts"][0]["sentences"]
    log(f"  → {len(sentences)} 句 (耗时 {int(time.time() - start)}s)")
    return sentences


# ─── Stage 3: 说话人分离 ──────────────────────────────────────────────

def diarize(audio_path: str, hf_token: str):
    """对本地音频做说话人分离，返回 pyannote Annotation 对象"""
    from pyannote.audio import Pipeline
    import torch

    # pyannote 需要 WAV 格式（MP3 帧边界导致采样数不匹配）
    wav_path = audio_path
    if not audio_path.lower().endswith(".wav"):
        wav_path = audio_path.rsplit(".", 1)[0] + "_diarize.wav"
        subprocess.run(
            ["ffmpeg", "-i", audio_path, "-ar", "16000", "-ac", "1", wav_path, "-y"],
            capture_output=True, check=True, timeout=300
        )

    log(f"  加载 pyannote 模型...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token,
    )
    if torch.backends.mps.is_available():
        pipeline.to(torch.device("mps"))
    elif torch.cuda.is_available():
        pipeline.to(torch.device("cuda"))

    log(f"  分析说话人...")
    output = pipeline(wav_path)

    # 清理临时 WAV
    if wav_path != audio_path and Path(wav_path).exists():
        Path(wav_path).unlink()

    # pyannote 4.x 返回 DiarizeOutput，需取 .speaker_diarization
    return output.speaker_diarization


def find_speaker(begin_ms: int, end_ms: int, diarization) -> str:
    """找到给定时间段内说话时间最长的说话人"""
    begin_s = begin_ms / 1000
    end_s = end_ms / 1000
    speaker_times: dict[str, float] = {}

    for turn, _, speaker in diarization.itertracks(yield_label=True):
        overlap_start = max(begin_s, turn.start)
        overlap_end = min(end_s, turn.end)
        if overlap_end > overlap_start:
            speaker_times[speaker] = speaker_times.get(speaker, 0) + (overlap_end - overlap_start)

    if not speaker_times:
        return "UNKNOWN"
    return max(speaker_times, key=speaker_times.get)


def assign_speakers(sentences: list[dict], diarization) -> list[dict]:
    """给每个句子分配说话人"""
    for s in sentences:
        s["speaker"] = find_speaker(s["begin_time"], s["end_time"], diarization)
    return sentences


# ─── 多段文件合并 ─────────────────────────────────────────────────────

def get_timestamp_from_filename(filename: str) -> datetime | None:
    """尝试从文件名解析时间戳（支持 DJI Mic 3 格式）"""
    name = Path(filename).stem
    parts = name.split("_")
    try:
        return datetime.strptime(parts[2] + parts[3], "%Y%m%d%H%M%S")
    except (IndexError, ValueError):
        return None


def merge_sentences(files_with_sentences: list[tuple[str, list]]) -> list[dict]:
    """合并多段音频的句子时间轴"""
    if len(files_with_sentences) == 1:
        return files_with_sentences[0][1]

    timestamps = [(f, get_timestamp_from_filename(f)) for f, _ in files_with_sentences]
    has_timestamps = all(ts is not None for _, ts in timestamps)

    all_sentences = []
    cumulative_offset_ms = 0

    for i, (filepath, sentences) in enumerate(files_with_sentences):
        if has_timestamps:
            base_time = timestamps[0][1]
            offset_ms = int((timestamps[i][1] - base_time).total_seconds() * 1000)
        else:
            offset_ms = cumulative_offset_ms

        for s in sentences:
            merged = dict(s)
            merged["begin_time"] = s["begin_time"] + offset_ms
            merged["end_time"] = s["end_time"] + offset_ms
            all_sentences.append(merged)

        if not has_timestamps and sentences:
            cumulative_offset_ms = max(s["end_time"] + offset_ms for s in sentences)

    all_sentences.sort(key=lambda x: x["begin_time"])
    return all_sentences


# ─── Stage 4: 格式化输出 ──────────────────────────────────────────────

def format_duration(ms: int) -> str:
    """毫秒转可读时长"""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def format_transcript_md(sentences: list[dict], source_files: list[str]) -> str:
    """生成可读的 .transcript.md"""
    if not sentences:
        return "# 转录结果\n\n（无内容）\n"

    duration = format_duration(max(s["end_time"] for s in sentences))
    speakers = sorted(set(s.get("speaker", "?") for s in sentences))
    speaker_info = f"{len(speakers)} 位" if len(speakers) > 1 else "1 位"
    sources = ", ".join(Path(f).name for f in source_files)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# 转录：{sources}",
        f"",
        f"> 时长：{duration} | 说话人：{speaker_info} | 转录时间：{now}",
        f"",
    ]

    for s in sentences:
        t = s["begin_time"] // 1000
        mm, ss = t // 60, t % 60
        speaker = s.get("speaker", "?")
        emotion = s.get("emotion", "")
        emotion_tag = f" [{emotion}]" if emotion and emotion != "neutral" else ""
        lines.append(f"[{mm:02d}:{ss:02d}] {speaker}{emotion_tag}: {s['text']}")

    return "\n".join(lines) + "\n"


def build_transcript_json(sentences: list[dict], source_files: list[str]) -> dict:
    """生成结构化 .transcript.json"""
    speakers = sorted(set(s.get("speaker", "?") for s in sentences))
    duration = max(s["end_time"] for s in sentences) if sentences else 0

    return {
        "source_files": [Path(f).name for f in source_files],
        "duration_seconds": duration // 1000,
        "speakers": speakers,
        "transcribed_at": datetime.now().isoformat(),
        "sentences": sentences,
    }


# ─── 主流程 ───────────────────────────────────────────────────────────

def process_single(file_path: str, normalized_dir: Path, output_dir: Path,
                   no_diarization: bool, hf_token: str | None) -> Path:
    """处理单个音频文件，返回 .transcript.md 路径"""
    name = Path(file_path).stem
    log(f"\n{'─' * 50}")
    log(f"处理: {Path(file_path).name}")

    log(f"\n[1/4] 标准化...")
    normalized = normalize_audio(file_path, normalized_dir)

    log(f"\n[2/4] 上传 + 转录...")
    url = upload_for_asr(normalized)
    sentences = transcribe_asr(url)

    if no_diarization:
        log(f"\n[3/4] 跳过说话人分离")
    elif not hf_token:
        log(f"\n[3/4] 跳过说话人分离（未提供 HF_TOKEN）")
    else:
        log(f"\n[3/4] 说话人分离...")
        dia = diarize(normalized, hf_token)
        sentences = assign_speakers(sentences, dia)

    log(f"\n[4/4] 输出...")
    output_dir.mkdir(parents=True, exist_ok=True)

    md_path = output_dir / f"{name}.transcript.md"
    json_path = output_dir / f"{name}.transcript.json"

    md_path.write_text(format_transcript_md(sentences, [file_path]), encoding="utf-8")
    json_path.write_text(
        json.dumps(build_transcript_json(sentences, [file_path]), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    log(f"  → {md_path}")
    log(f"  → {json_path}")
    return md_path


def process_merged(file_paths: list[str], normalized_dir: Path, output_dir: Path,
                   no_diarization: bool, hf_token: str | None) -> Path:
    """多段文件合并为一份转录"""
    name = Path(file_paths[0]).stem + "_merged"
    log(f"\n{'─' * 50}")
    log(f"合并处理: {len(file_paths)} 个文件")

    log(f"\n[1/4] 标准化...")
    normalized_files = []
    for f in file_paths:
        normalized_files.append(normalize_audio(f, normalized_dir))

    log(f"\n[2/4] 上传 + 转录...")
    files_with_sentences = []
    for orig, norm in zip(file_paths, normalized_files):
        url = upload_for_asr(norm)
        sentences = transcribe_asr(url)
        files_with_sentences.append((orig, sentences))

    sentences = merge_sentences(files_with_sentences)
    log(f"  合计 {len(sentences)} 句")

    if no_diarization:
        log(f"\n[3/4] 跳过说话人分离")
    elif not hf_token:
        log(f"\n[3/4] 跳过说话人分离（未提供 HF_TOKEN）")
    else:
        log(f"\n[3/4] 说话人分离...")
        if len(normalized_files) > 1:
            log("  提示: 多段文件当前仅对第一段做说话人分析")
        dia = diarize(normalized_files[0], hf_token)
        sentences = assign_speakers(sentences, dia)

    log(f"\n[4/4] 输出...")
    output_dir.mkdir(parents=True, exist_ok=True)

    md_path = output_dir / f"{name}.transcript.md"
    json_path = output_dir / f"{name}.transcript.json"

    md_path.write_text(format_transcript_md(sentences, file_paths), encoding="utf-8")
    json_path.write_text(
        json.dumps(build_transcript_json(sentences, file_paths), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    log(f"  → {md_path}")
    log(f"  → {json_path}")
    return md_path


def main():
    parser = argparse.ArgumentParser(
        description="录音转录 — 将音频文件转为结构化文本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s meeting.m4a                            # 单文件
  %(prog)s *.m4a --output-dir ./transcripts/      # 批量 + 指定输出
  %(prog)s seg1.wav seg2.wav --merge              # 多段合并
  %(prog)s audio.mp3 --no-diarization             # 跳过说话人分离
        """
    )
    parser.add_argument("files", nargs="+", help="音频文件路径")
    parser.add_argument("--output-dir", help="转录输出目录（默认：源文件同目录）")
    parser.add_argument("--merge", action="store_true",
                        help="多文件视为同一场会议，合并时间轴输出一份转录")
    parser.add_argument("--no-diarization", action="store_true",
                        help="跳过说话人分离")
    parser.add_argument("--diarize-only", action="store_true",
                        help="仅补跑说话人分离（复用已有的 .transcript.json）")
    parser.add_argument("--hf-token", default=os.getenv("HF_TOKEN"),
                        help="HuggingFace token（默认读 HF_TOKEN 环境变量）")
    args = parser.parse_args()

    # 延迟导入（dashscope 导入较慢，放到确认参数合法之后）
    global requests, dashscope, QwenTranscription
    import requests
    import dashscope
    from dashscope.audio.qwen_asr import QwenTranscription

    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    if not dashscope.api_key:
        log("错误: 请设置 DASHSCOPE_API_KEY 环境变量")
        sys.exit(1)
    dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

    # 验证文件
    for f in args.files:
        p = Path(f)
        if not p.exists():
            log(f"错误: 文件不存在 — {f}")
            sys.exit(1)
        if not is_audio_file(f):
            log(f"警告: {p.name} 不是常见音频格式，将尝试处理")

    batch_id = uuid.uuid4().hex[:8]
    normalized_dir = Path(f"/tmp/audio-transcribe/{batch_id}")
    normalized_dir.mkdir(parents=True, exist_ok=True)

    output_dir = Path(args.output_dir) if args.output_dir else Path(args.files[0]).parent

    log(f"批次: {batch_id}")
    log(f"文件: {len(args.files)} 个")
    log(f"临时目录: {normalized_dir}")
    log(f"输出目录: {output_dir}")

    # ── diarize-only 模式：复用已有转录，仅补跑说话人分离 ──
    if args.diarize_only:
        if not args.hf_token:
            log("错误: --diarize-only 需要 HF_TOKEN")
            sys.exit(1)

        for f in args.files:
            src = Path(f)
            # 找到对应的 .transcript.json（同目录或 output-dir）
            json_candidates = [
                output_dir / f"{src.stem}.transcript.json",
                src.parent / f"{src.stem}.transcript.json",
            ]
            json_path = next((p for p in json_candidates if p.exists()), None)
            if not json_path:
                log(f"错误: 找不到 {src.stem}.transcript.json（在 {output_dir} 或 {src.parent}）")
                sys.exit(1)

            log(f"\n{'─' * 50}")
            log(f"补跑说话人分离: {src.name}")
            log(f"  复用转录: {json_path}")

            data = json.loads(json_path.read_text(encoding="utf-8"))
            sentences = data["sentences"]
            log(f"  已有 {len(sentences)} 句")

            # 标准化音频（diarization 需要本地音频）
            log(f"\n[1/3] 标准化音频...")
            normalized = normalize_audio(str(src), normalized_dir)

            log(f"\n[2/3] 说话人分离...")
            dia = diarize(normalized, args.hf_token)
            sentences = assign_speakers(sentences, dia)

            log(f"\n[3/3] 重新输出...")
            md_path = output_dir / f"{src.stem}.transcript.md"

            md_path.write_text(
                format_transcript_md(sentences, [str(src)]), encoding="utf-8"
            )
            # 更新 json（加入 speaker 字段）
            data["sentences"] = sentences
            data["speakers"] = sorted(set(s.get("speaker", "?") for s in sentences))
            json_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            log(f"  → {md_path}")

        log(f"\n{'═' * 50}")
        log(f"✅ 说话人分离补跑完成!")
        log(f"{'═' * 50}")
        sys.exit(0)

    try:
        if args.merge:
            result = process_merged(
                args.files, normalized_dir, output_dir,
                args.no_diarization, args.hf_token
            )
            results = [result]
        else:
            results = []
            for f in args.files:
                result = process_single(
                    f, normalized_dir, output_dir,
                    args.no_diarization, args.hf_token
                )
                results.append(result)

        log(f"\n{'═' * 50}")
        log(f"✅ 完成! 共处理 {len(args.files)} 个文件")
        for r in results:
            log(f"  {r}")
        log(f"{'═' * 50}")

    except Exception as e:
        log(f"\n{'═' * 50}")
        log(f"❌ 失败: {e}")
        log(f"{'═' * 50}")
        sys.exit(1)


if __name__ == "__main__":
    main()
