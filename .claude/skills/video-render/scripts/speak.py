#!/usr/bin/env python3
"""Render a spoken script to MP3 in the Voice A voice-over (carried over from the Genesis project by the user's choice, 2026-10-04).

Usage: speak.py SCRIPT.txt OUT.mp3 [--title "..."] [--timing OUT.json]
Paragraphs are separated by blank lines. Run setup.sh first.
--timing writes each paragraph's start and end second (and text) so a video can be synced to the voice
(added 2026-10-04 for the video-render skill; the audio itself is unchanged).
"""
import argparse, os, re, subprocess, sys, tempfile
import numpy as np
import soundfile as sf
from scipy.signal import butter, lfilter
from kokoro_onnx import Kokoro

CACHE = os.environ.get("VP_TTS_CACHE", "/tmp/kokoro")
# Model file inside CACHE. The user chose the full-precision model on 2026-10-04 after listening to an A/B/C
# comparison ("C seems good already"): kokoro-v1.0.onnx (same voice file as before). If it is missing the
# smaller fp16 file is used; VP_TTS_MODEL overrides both.
MODEL = os.environ.get("VP_TTS_MODEL") or ("kokoro-v1.0.onnx" if os.path.exists(f"{CACHE}/kokoro-v1.0.onnx") else "kokoro-v1.0.fp16.onnx")

# Default voice. Change only if the user asks for a different voice.
VOICE_MIX = {"af_bella": 0.55, "af_nova": 0.45}
SPEED = 1.0
PARAGRAPH_PAUSE_S = 0.35
# (type, freq Hz, gain dB, Q): trims low-mid warmth, lifts presence for a crisper delivery.
EQ = [("shelf", 250, -3.0, 0.7), ("peak", 3500, 3.5, 0.9), ("peak", 6500, 1.5, 1.2)]
HIGHPASS_HZ = 90
PEAK = 0.89  # about -1 dBFS
BITRATE_KBPS = 128


# Pronunciation fixes (user complaint 2026-10-04: "your pronounce is not too good"). Found by reading the
# phonemes Kokoro's tokenizer produces, not by ear:
# 1. A hyphen between letters fuses the words ("twenty-nine" -> "twentynine", "ten-year" -> "tenyear") and
#    drops the second word's stress, so hyphens between letters become spaces.
# 2. Indonesian names the American-English rules get wrong: "Jakarta" came out with a flapped "d"
#    (ja-KAR-duh), "rupiah" as "roo-PIE-uh". Keys are the tokenizer's output for the word, values the fix.
PRONUNCIATION = {
    "dʒɐkˈɑːɹɾə": "dʒɑːkˈɑːɹtə",   # Jakarta
    "ɹˈuːpˈaɪə": "ɹuːpˈiːɑː",       # rupiah
    "nˈæsdæk": "nˈæzdæk",           # Nasdaq
}


def fix_text(t):
    return re.sub(r"(?<=[A-Za-z])-(?=[A-Za-z])", " ", t)


def to_phonemes(k, text):
    ph = k.tokenizer.phonemize(fix_text(text), "en-us")
    for a, b in PRONUNCIATION.items():
        ph = ph.replace(a, b)
    return ph


def biquad(kind, f0, gain_db, q, sr):
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f0 / sr
    c, s = np.cos(w), np.sin(w)
    al = s / (2 * q)
    if kind == "peak":
        b = [1 + al * A, -2 * c, 1 - al * A]
        a = [1 + al / A, -2 * c, 1 - al / A]
    else:
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * c + sq), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - sq)]
        a = [(A + 1) + (A - 1) * c + sq, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sq]
    return np.array(b) / a[0], np.array(a) / a[0]


def sharpen(x, sr):
    b, a = butter(2, HIGHPASS_HZ / (sr / 2), "high")
    x = lfilter(b, a, x)
    for kind, f0, g, q in EQ:
        b, a = biquad(kind, f0, g, q, sr)
        x = lfilter(b, a, x)
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("out")
    ap.add_argument("--title", default="Video voice-over")
    ap.add_argument("--timing", default=None, help="write per-paragraph start/end seconds as JSON")
    args = ap.parse_args()

    paras = [p.strip().replace("\n", " ") for p in open(args.script).read().split("\n\n") if p.strip()]
    if not paras:
        sys.exit("empty script")

    k = Kokoro(f"{CACHE}/{MODEL}", f"{CACHE}/voices-v1.0.bin")
    voice = sum(k.get_voice_style(n) * w for n, w in VOICE_MIX.items()).astype(np.float32)

    parts, sr, slow, timing, cursor = [], 24000, [], [], 0.0
    for i, p in enumerate(paras):
        a, sr = k.create(to_phonemes(k, p), voice=voice, speed=SPEED, lang="en-us", is_phonemes=True)
        secs = len(a) / sr
        wpm = len(p.split()) / secs * 60 if secs else 0
        if not 90 <= wpm <= 220:
            slow.append(f"paragraph {i + 1}: {wpm:.0f} wpm")
        timing.append({"i": i + 1, "start": round(cursor, 3), "end": round(cursor + secs, 3), "text": p})
        cursor += secs + PARAGRAPH_PAUSE_S
        parts += [a, np.zeros(int(sr * PARAGRAPH_PAUSE_S), dtype=a.dtype)]

    x = sharpen(np.concatenate(parts), sr)
    x = (x / np.abs(x).max() * PEAK).astype(np.float32)

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, x, sr)
        subprocess.run(["lame", "--quiet", "-b", str(BITRATE_KBPS), "--tt", args.title,
                        "--ta", "Video-publishing", tmp.name, args.out], check=True)

    if args.timing:
        import json
        json.dump({"duration": round(len(x) / sr, 3), "paragraphs": timing}, open(args.timing, "w"), indent=1)
    mins, secs = divmod(round(len(x) / sr), 60)
    print(f"wrote {args.out}: {mins}:{secs:02d}, {len(paras)} paragraphs")
    for s in slow:
        print(f"CHECK pace outside normal range, {s}")


if __name__ == "__main__":
    main()
