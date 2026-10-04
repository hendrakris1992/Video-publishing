#!/usr/bin/env bash
# Idempotent setup for video rendering: Playwright bindings (the browser is pre-installed, never run
# `playwright install`), imageio-ffmpeg (a bundled static ffmpeg with libx264; PyPI works from the
# sandbox, system ffmpeg is not installed), and two Google Fonts downloaded once into /tmp/video-publishing/fonts
# (fonts.googleapis.com and fonts.gstatic.com are reachable; cdnjs, jsDelivr and unpkg are NOT, so scenes
# must not load libraries or fonts from a CDN). Safe to re-run.
set -euo pipefail
python3 -c "import playwright" 2>/dev/null || pip install -q playwright 2>&1 | grep -v "WARNING: Running pip" || true
python3 -c "import imageio_ffmpeg" 2>/dev/null || pip install -q imageio-ffmpeg 2>&1 | grep -v "WARNING: Running pip" || true
python3 "$(dirname "$0")/fetch_fonts.py"
python3 -c "import playwright, imageio_ffmpeg; print('video-render: ready (ffmpeg:', imageio_ffmpeg.get_ffmpeg_exe(), ')')"
