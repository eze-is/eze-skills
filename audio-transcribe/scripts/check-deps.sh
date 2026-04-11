#!/bin/bash
# audio-transcribe 环境依赖检查

# 从 ~/.claude/.env 加载密钥（环境变量优先）
CLAUDE_ENV="$HOME/.claude/.env"
if [ -f "$CLAUDE_ENV" ]; then
    while IFS='=' read -r key value; do
        [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
        value="${value%\"}" && value="${value#\"}"
        [ -z "${!key}" ] && export "$key=$value"
    done < "$CLAUDE_ENV"
fi

echo "🔍 检查 audio-transcribe 依赖..."
echo ""

ALL_OK=true

# ffmpeg
if command -v ffmpeg &>/dev/null; then
    echo "✅ ffmpeg: $(ffmpeg -version 2>&1 | head -1 | cut -d' ' -f3)"
else
    echo "❌ ffmpeg: 未安装 → brew install ffmpeg"
    ALL_OK=false
fi

# Python dashscope
if python3 -c "import dashscope" 2>/dev/null; then
    DASH_VER=$(python3 -c 'import importlib.metadata; print(importlib.metadata.version("dashscope"))' 2>/dev/null || echo "已安装")
    echo "✅ dashscope: $DASH_VER"
else
    echo "❌ dashscope: 未安装 → pip install dashscope"
    ALL_OK=false
fi

# DASHSCOPE_API_KEY
if [ -n "$DASHSCOPE_API_KEY" ]; then
    echo "✅ DASHSCOPE_API_KEY: 已设置"
else
    echo "❌ DASHSCOPE_API_KEY: 未设置 → export DASHSCOPE_API_KEY=your_key"
    ALL_OK=false
fi

# pyannote (可选)
echo ""
echo "── 可选依赖（说话人分离）──"
if python3 -c "import pyannote.audio" 2>/dev/null; then
    echo "✅ pyannote.audio: 已安装"
else
    echo "⚠️  pyannote.audio: 未安装 → pip install pyannote.audio（跳过说话人分离时不需要）"
fi

# HF_TOKEN：仅在 pyannote 模型未缓存时才需要
PYANNOTE_CACHED=true
for model in "models--pyannote--speaker-diarization-3.1" "models--pyannote--segmentation-3.0"; do
    if [ ! -d "$HOME/.cache/huggingface/hub/$model" ]; then
        PYANNOTE_CACHED=false
        break
    fi
done

if $PYANNOTE_CACHED; then
    echo "✅ pyannote 模型: 已缓存（无需 HF_TOKEN）"
elif [ -n "$HF_TOKEN" ]; then
    echo "✅ HF_TOKEN: 已设置"
else
    echo "⚠️  HF_TOKEN: 未设置 → pyannote 模型未缓存，首次使用需要 HF_TOKEN 下载模型"
fi

echo ""
if $ALL_OK; then
    echo "✅ 核心依赖全部就绪"
    exit 0
else
    echo "❌ 有依赖未满足，请先安装"
    exit 1
fi
