#!/usr/bin/env bash
# Idempotent setup for the video voice-over: Kokoro TTS + LAME. Safe to re-run.
set -euo pipefail
CACHE="${VP_TTS_CACHE:-/tmp/kokoro}"
REL="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"

python3 -c "import kokoro_onnx, soundfile, scipy" 2>/dev/null \
  || pip install -q kokoro-onnx soundfile scipy 2>&1 | grep -v "WARNING: Running pip" || true

if ! command -v lame >/dev/null; then
  apt-get update -qq >/dev/null 2>&1 || true
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq lame >/dev/null
fi

mkdir -p "$CACHE"
for f in kokoro-v1.0.onnx kokoro-v1.0.fp16.onnx voices-v1.0.bin; do
  [ -s "$CACHE/$f" ] || curl -sSL -m 600 -o "$CACHE/$f" "$REL/$f"
done

python3 -c "import kokoro_onnx, soundfile, scipy" && command -v lame >/dev/null \
  && ls "$CACHE"/kokoro-v1.0.fp16.onnx "$CACHE"/voices-v1.0.bin >/dev/null \
  && echo "voice: ready ($CACHE)"
