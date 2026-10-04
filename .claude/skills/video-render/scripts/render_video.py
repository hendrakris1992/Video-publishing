#!/usr/bin/env python3
"""Render a deterministic HTML motion-graphics scene to an MP4 (H.264 + AAC), frame by frame.

Usage: render_video.py SCENE.html OUT.mp4 [--audio VOICE.mp3] [--fps 30] [--size 1080x1920]
                       [--duration SECONDS] [--tail 0.6] [--still T --out-png FILE.png]

The scene contract (the scene is plain HTML, no external libraries or CDN):
  window.__duration  seconds of animation the scene wants (number)
  window.__seek(t)   draw the exact state of the scene at time t seconds (pure function of t: no timers,
                     no requestAnimationFrame, no Date.now, no Math.random without a fixed seed)
The renderer loads the page, waits for fonts, then for every frame calls __seek(frame/fps), screenshots
the page and pipes it to ffmpeg. Because time is driven by the renderer, the output is frame-accurate and
identical on every run, and rendering speed does not affect animation speed.
--still T renders only the frame at time T to a PNG (use it to check layout before a full render).
Fonts: scripts/fetch_fonts.py (run setup.sh) writes /tmp/video-publishing/fonts/fonts.css; it is injected
automatically, so a scene can use font-family 'Sora' (display) and 'Inter' (text and figures).
"""
import argparse
import glob
import math
import os
import subprocess
import sys
import time

FONTS_CSS = "/tmp/video-publishing/fonts/fonts.css"


def find_chromium():
    c = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))
    if not c:
        sys.exit("No pre-installed Chromium under /opt/pw-browsers. Do not run 'playwright install'; tell the user.")
    return c[-1]


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("imageio-ffmpeg missing: run bash .claude/skills/video-render/scripts/setup.sh")


def audio_seconds(ff, path):
    r = subprocess.run([ff, "-i", path], capture_output=True, text=True)
    import re
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0


def _worker(args):
    scene, w, h, ss, fps, quality, scene_dur, lo, hi, folder = args
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=find_chromium(), args=["--no-sandbox", "--force-color-profile=srgb"])
        pg = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=ss)
        pg.goto("file://" + os.path.abspath(scene))
        if os.path.exists(FONTS_CSS):
            pg.add_style_tag(path=FONTS_CSS)
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(400)
        for i in range(lo, hi):
            pg.evaluate(f"window.__seek({min(i / fps, scene_dur):.5f})")
            pg.screenshot(path=f"{folder}/f{i:06d}.jpg", type="jpeg", quality=quality)
        br.close()
    return hi - lo


def render_parallel(a, ff, w, h, scene_dur, n):
    import shutil, tempfile
    from concurrent.futures import ProcessPoolExecutor
    folder = tempfile.mkdtemp(prefix="vp-frames-")
    t0 = time.time()
    k = a.workers
    step = math.ceil(n / k)
    jobs = [(a.scene, w, h, a.ss, a.fps, a.quality, scene_dur, i * step, min(n, (i + 1) * step), folder) for i in range(k) if i * step < n]
    with ProcessPoolExecutor(max_workers=k) as ex:
        list(ex.map(_worker, jobs))
    print(f"  {n} frames written in {time.time() - t0:.0f}s ({k} workers); encoding", flush=True)
    vf = ["-vf", f"scale={w}:{h}:flags=lanczos"] if a.ss > 1 else []
    cmd = [ff, "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", f"{folder}/f%06d.jpg"]
    if a.audio:
        cmd += ["-i", a.audio]
    cmd += vf + ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(a.fps)]
    if a.audio:
        cmd += ["-c:a", "aac", "-b:a", "160k", "-af", "apad", "-t", f"{n / a.fps:.3f}"]
    cmd += ["-movflags", "+faststart", a.out]
    rc = subprocess.run(cmd).returncode
    shutil.rmtree(folder, ignore_errors=True)
    if rc:
        sys.exit(f"ffmpeg failed (exit {rc})")
    print(f"wrote {a.out}: {n / a.fps:.1f}s, {a.fps} fps, {w}x{h}, {os.path.getsize(a.out) / 1e6:.1f} MB, rendered in {time.time() - t0:.0f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("out")
    ap.add_argument("--audio")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--duration", type=float)
    ap.add_argument("--tail", type=float, default=0.6, help="seconds of picture kept after the audio ends")
    ap.add_argument("--still", type=float)
    ap.add_argument("--quality", type=int, default=92, help="JPEG quality of the frames fed to ffmpeg")
    ap.add_argument("--ss", type=int, default=1, help="supersampling factor (2 = render at 2x and scale down: removes the glyph-snapping shimmer of slow moves)")
    ap.add_argument("--workers", type=int, default=1, help="parallel Chromium processes (frames go to a temp folder, then ffmpeg)")
    a = ap.parse_args()
    w, h = (int(v) for v in a.size.lower().split("x"))

    from playwright.sync_api import sync_playwright
    ff = ffmpeg_exe()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=find_chromium(), args=["--no-sandbox", "--force-color-profile=srgb"])
        pg = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=a.ss)
        pg.goto("file://" + os.path.abspath(a.scene))
        if os.path.exists(FONTS_CSS):
            pg.add_style_tag(path=FONTS_CSS)
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(400)
        if not pg.evaluate("typeof window.__seek === 'function' && typeof window.__duration === 'number'"):
            sys.exit("scene must define window.__seek(t) and window.__duration (see the docstring)")
        scene_dur = pg.evaluate("window.__duration")
        if a.still is not None:
            pg.evaluate(f"window.__seek({a.still})")
            out = a.out
            pg.screenshot(path=out, type="png")
            print(f"wrote still {out} at t={a.still}s")
            br.close()
            return
        dur = a.duration or scene_dur
        if a.audio:
            dur = max(dur, audio_seconds(ff, a.audio) + a.tail)
        n = int(math.ceil(dur * a.fps))
        if a.workers > 1:
            br.close()
            return render_parallel(a, ff, w, h, scene_dur, n)
        vf = ["-vf", f"scale={w}:{h}:flags=lanczos"] if a.ss > 1 else []
        cmd = [ff, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(a.fps), "-c:v", "mjpeg", "-i", "-"]
        if a.audio:
            cmd += ["-i", a.audio]
        cmd += vf + ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(a.fps)]
        if a.audio:
            cmd += ["-c:a", "aac", "-b:a", "160k", "-af", "apad", "-t", f"{n / a.fps:.3f}"]
        cmd += ["-movflags", "+faststart", a.out]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        t0 = time.time()
        for i in range(n):
            pg.evaluate(f"window.__seek({min(i / a.fps, scene_dur):.5f})")
            proc.stdin.write(pg.screenshot(type="jpeg", quality=a.quality))
            if i and i % (a.fps * 10) == 0:
                print(f"  {i}/{n} frames, {time.time() - t0:.0f}s elapsed", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        br.close()
    if rc:
        sys.exit(f"ffmpeg failed (exit {rc})")
    size = os.path.getsize(a.out) / 1e6
    print(f"wrote {a.out}: {n / a.fps:.1f}s, {a.fps} fps, {w}x{h}, {size:.1f} MB, rendered in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
