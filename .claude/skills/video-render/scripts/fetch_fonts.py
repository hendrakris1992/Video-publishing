#!/usr/bin/env python3
"""Download the video fonts once into /tmp/video-publishing/fonts and write fonts.css (local @font-face).

Display: Sora 600/800. Text and numbers: Inter 500/700 (use font-variant-numeric: tabular-nums for figures).
Source: Google Fonts CSS API (both fonts are open source under the SIL Open Font License).
"""
import os, re, subprocess, sys

DEST = "/tmp/video-publishing/fonts"
FAMILIES = [("Sora", "600;800"), ("Inter", "500;700")]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def curl(url, out=None):
    cmd = ["curl", "-sS", "-m", "40", "-A", UA, url] + (["-o", out] if out else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"font download failed for {url}: {r.stderr[:200]}")
    return r.stdout


REPO_FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts")


def from_repo():
    """Copy the fonts committed in assets/fonts (no network, 2026-10-04) and write fonts.css. True on success."""
    import shutil
    faces = [("Sora", 600), ("Sora", 800), ("Inter", 500), ("Inter", 700)]
    if not all(os.path.exists(os.path.join(REPO_FONTS, f"{f}-{w}.woff2")) for f, w in faces):
        return False
    os.makedirs(DEST, exist_ok=True)
    css = []
    for fam, w in faces:
        shutil.copy(os.path.join(REPO_FONTS, f"{fam}-{w}.woff2"), DEST)
        css.append(f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;"
                   f"src:url('file://{DEST}/{fam}-{w}.woff2') format('woff2');}}")
    open(os.path.join(DEST, "fonts.css"), "w").write("\n".join(css) + "\n")
    print(f"fonts: copied 4 faces from the repo to {DEST}")
    return True


def main():
    css_path = os.path.join(DEST, "fonts.css")
    if os.path.exists(css_path) and len(os.listdir(DEST)) > 3:
        print("fonts: already present")
        return
    if from_repo():
        return
    os.makedirs(DEST, exist_ok=True)
    out_css = []
    for fam, weights in FAMILIES:
        css = curl(f"https://fonts.googleapis.com/css2?family={fam}:wght@{weights}&display=swap")
        for block in re.findall(r"@font-face\s*\{.*?\}", css, flags=re.S):
            url = re.search(r"url\((https://[^)]+\.woff2)\)", block)
            weight = re.search(r"font-weight:\s*(\d+)", block)
            rng = re.search(r"unicode-range:\s*([^;]+);", block)
            if not url or not weight:
                continue
            # keep only the Latin subset (its unicode-range starts at U+0000)
            if rng and not rng.group(1).strip().startswith("U+0000"):
                continue
            fname = f"{fam}-{weight.group(1)}.woff2"
            curl(url.group(1), os.path.join(DEST, fname))
            out_css.append(f"@font-face{{font-family:'{fam}';font-weight:{weight.group(1)};font-style:normal;"
                           f"src:url('file://{DEST}/{fname}') format('woff2');}}")
    if len(out_css) < 4:
        sys.exit(f"only {len(out_css)} font faces found; expected 4")
    open(css_path, "w").write("\n".join(out_css) + "\n")
    print(f"fonts: wrote {len(out_css)} faces to {DEST}")


if __name__ == "__main__":
    main()
