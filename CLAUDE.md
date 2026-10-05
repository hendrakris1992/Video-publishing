# Video-publishing

Short promotional videos (first project: clothing promotion), produced as programmatic motion graphics by the **Chris** agent (`.claude/agents/chris.md`) with the `video-render` skill (`.claude/skills/video-render/`). Separate from the Genesis market-research repo (`agentic-ai`); none of its research, audit or Permata Bank rules apply here.

## Rules
- **No invented facts.** Every price, discount, date, product name, material, size or claim on screen or in the voice-over comes from the user. If something is missing, ask; do not guess. Chris lists every claim in his storyboard so the user can check it before rendering.
- **Truthful promos.** Do not state or imply discounts, "limited stock", ratings or testimonials that the user has not supplied. Flag any claim that could be a regulated advertising claim (e.g. "cheapest", "100% cotton") for the user to confirm.
- **Assets:** use the user's product photos and logo. No stock footage, no music (no licensed audio available), no AI-generated imagery unless the user explicitly asks (and OKs any credit spend first).
- **Voice:** Voice A (Kokoro, 55% `af_bella` + 45% `af_nova`; `scripts/speak.py` is the source of truth), carried over from Genesis by default. Change only if the user asks. Exception, decided by the user: Indonesian videos are silent with captions only (Voice A is English-only).
- **Look defaults:** vertical 1080x1920, 30 fps (final 60 fps), Sora + Inter, short captions on, 15 to 30 seconds. Brand colours/fonts override when the user provides them.
- **Workflow:** Stage 1 storyboard + claims list, user approves; Stage 2 build and render. No publishing: files go to the user via `SendUserFile`. Commit and push to GitHub only when asked.
- Use the user's own wording for the brand; reply in the language they write in.

## Layout
- `.claude/agents/chris.md`: the video producer agent.
- `.claude/agents/scriptwriter.md`: the voice-over scriptwriter (English or Indonesian, playful); its approved script feeds Chris.
- `.claude/agents/webdev.md`: UI designer + front-end coder for simple single-file HTML pages that open offline on iPhone; output goes to `apps/<name>/index.html`.
- `.claude/skills/video-render/`: scene template, fonts, `scripts/` (setup, voice, render).
- `videos/<project>/`: per-video storyboard, scene HTML, script, final MP4 (add when a video is made).

## Status
Pipeline copied from the Genesis repo on 2026-10-04 and path-renamed. Tested in this repo on 2026-10-04: `setup.sh`, a still render and an 11 s silent 1080x1920 MP4 render of the template (330 frames, 15 s). NOT yet tested in this repo: `voice_setup.sh` and `speak.py` (Kokoro model download, voice-over, timing JSON) and rendering with audio; the scene template is still a finance sample and has no promo scenes yet.
