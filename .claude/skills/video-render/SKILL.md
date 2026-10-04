---
name: video-render
description: Turn a scripted HTML motion-graphics scene into an MP4 (vertical 1080x1920 by default, or any size) with Voice A voice-over and burned-in captions, frame-accurate and reproducible. Use when the user asks for a promo video, reel or short clip, or when the Chris agent renders a storyboard. Not for AI-generated footage.
---

# Video render

Method: deterministic motion graphics. A scene is one HTML file whose picture is a pure function of time, `window.__seek(t)`. The renderer steps through time frame by frame, screenshots each frame in headless Chromium and pipes it to ffmpeg. Product photos supplied by the user can be placed in the scene as `<img>` (local files, base64 or relative paths).

Carried over from the Genesis repo (tested there on 2026-10-04); re-test here before relying on it (see CLAUDE.md "Status").

## 1. Set up (every new session)
```bash
bash .claude/skills/video-render/scripts/setup.sh        # playwright bindings, imageio-ffmpeg (bundled ffmpeg), Sora and Inter fonts
bash .claude/skills/video-render/scripts/voice_setup.sh  # Voice A (Kokoro) + lame
```
Observed in the Genesis cloud sandbox: PyPI, fonts.googleapis.com and fonts.gstatic.com reachable; cdnjs, jsDelivr and unpkg NOT, so scenes must be vanilla HTML, CSS, SVG and JavaScript with no CDN libraries. System ffmpeg may be missing; imageio-ffmpeg provides one. Never run `playwright install` (Chromium is pre-installed).

## 2. The scene contract
Start from `assets/scene_template.html` (copy to the scratchpad). It defines `window.__duration` and `window.__seek(t)` (pure function of `t`: no timers, no `requestAnimationFrame`, no `Date.now`, no unseeded `Math.random`), a `DATA` object at the top that holds every text, price and caption on screen (filled only from what the user supplied), helpers `pr` (eased progress), `fmt`, `E` (HTML escape: always use for text going into `innerHTML`). The template is a finance sample (count-up number, bar chart); replace those scenes with promo scenes (product shot, price/offer, call to action). `DATA.sample = true` stamps a SAMPLE watermark; set false only when every value is real.
Layout for 1080x1920: safe area 72 px sides, 220 px top, 380 px bottom (phone overlays). Fonts: Sora (display), Inter (text).

## 3. Voice-over and captions
```bash
python3 .claude/skills/video-render/scripts/speak.py SCRIPT.txt VO.mp3 --title "..." --timing VO.json
```
One paragraph per scene line (blank line between). `VO.json` gives each paragraph's `start` and `end`: use them for scene times and `DATA.captions`. Voice A only unless the user asks otherwise.

## 4. Check, then render
```bash
python3 .claude/skills/video-render/scripts/render_video.py SCENE.html OUT.png --still 4.2     # one frame; READ the PNG
python3 .claude/skills/video-render/scripts/render_video.py SCENE.html OUT.mp4 --audio VO.mp3 --fps 60 --ss 2 --workers 4 --size 1080x1920
```
Render stills at the key moments of every scene and read them first (text cut off, under the caption band, overlaps, contrast, outside the safe area). Defaults for final renders: `--fps 60 --ss 2 --workers 4`.

## 5. Verify the file
`ffmpeg -i OUT.mp4` (bundled binary: `python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"`) must show one H.264 video stream at the requested size and one AAC audio stream; duration matches voice-over plus tail. Report duration and size. Send with `SendUserFile`, `display: "attach"`.

## Motion rules
Entrances 0.5 to 0.8 s with a quartic or exponential ease-out; keep the camera moving through a cut; cross-fade scenes over 0.2 s with a small slide or scale. Measured on one scene in the Genesis project: `--ss 2` reduced text shimmer in slow moves (0.20 px to 0.09 px RMS deviation); a proxy, not a verdict on how it looks.
