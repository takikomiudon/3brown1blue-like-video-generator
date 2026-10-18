# Manim Video Lab

Production pipeline for mathematical and technical animations using [Manim Community Edition](https://www.manim.community/).

This skill is Docker-first so users do not need to install Manim, LaTeX, or ffmpeg directly on their machine. Setup builds a small local image, `manim-video-runtime:v0.20.1`, from the pinned official `manimcommunity/manim:v0.20.1` base plus ffmpeg, then writes outputs back into the project directory.

## Attribution

This project is built with gratitude for Manim, the open-source mathematical animation engine originally written by [Grant Sanderson](https://github.com/3b1b/manim) and now maintained by the [Manim Community](https://www.manim.community/). It is an independent helper skill for agent workflows and is not affiliated with or endorsed by Grant Sanderson, 3Blue1Brown, or the Manim Community.

## Maintainer

Created and maintained by [Rakesh Sahni](https://x.com/rakeshsahni_).

For bugs and feature requests, please open a GitHub issue. For quick questions, suggestions, or feedback, you can also reach me on X.

## License

MIT. See [LICENSE](LICENSE).

## What It Does

Creates 3Blue1Brown-style animated videos from text prompts. The agent handles creative planning, Python scene generation, rendering, scene stitching, and iterative refinement.

For ambitious output, the skill uses a director-packet workflow before coding: extract the core insight, prompt objects, object/symbol ledgers, beat graph, layout zones, focus handoffs, camera purpose, pacing, payoff frame, source anchors, and preflight gates. This is the main quality layer that keeps outputs from becoming generic slide-like Manim scenes.

Key quality references:

- `references/director-packet.md` - portable Text2Animation-style directing contract.
- `references/preflight-gates.md` - contract, prompt-preservation, LMIR, operator, source-anchor, direction-execution, assertion, visual-audit, and review gates.
- `references/attention-and-retention.md` - quantified retention grammar mined from the 3Blue1Brown source corpus: change cadence, attention thread, camera fusion, overlap dial, hook architecture, and a deterministic dead-air audit.
- `references/source-backed-patterns.md` - distilled Manim pattern atlas: stable scaffolds, live drivers, inspectors, memory rails, dual-space stages, state-space zooms, and template selection.
- `references/algorithm-choreography.md` - logical motion for algorithm and data-structure videos: sync law, state-to-style contracts, swap/compare/traversal idioms, synced pseudocode panels, and step-trace-driven choreography.
- `references/codegen-craft.md` - current-Manim implementation guardrails for token-safe morphs, rate functions, live dependencies, stable inspectors, protected lanes, and source anchors.
- `references/visual-polish.md` - the premium finish layer: glow, sheen, spotlight dimmers, micro-motion, organic entrances, and a strict polish budget.
- `references/worked-example.md` - a complete render-verified exemplar scene with its mini director packet, showing the full doctrine stack operating in ~100 lines.
- `references/review-loop.md` - direct video review or Docker/ffmpeg frame extraction fallback with bounded repair passes, plus an ffmpeg freezedetect dead-air scan.

Use cases:

- Concept explainers: "Explain how neural networks learn"
- Equation derivations: "Animate the proof of the Pythagorean theorem"
- Algorithm visualizations: "Show how quicksort works step by step"
- Data stories: "Animate our before/after performance metrics"
- Architecture diagrams: "Show our microservice architecture building up"

## Install The Skill

This is an Agent Skills package, not a Codex-only package. The portable core is `SKILL.md` plus bundled `scripts/` and `references/`. The `agents/openai.yaml` file is optional OpenAI/Codex UI metadata; other tools can ignore it.

Keep the folder intact:

```text
manim-video/
  Dockerfile
  SKILL.md
  scripts/      # Bash and PowerShell Docker wrappers
  references/
  agents/
```

Install the folder as `manim-video` so it matches `name: manim-video` in `SKILL.md`. If you clone a repository with another folder name, rename it when copying into a skills directory.

Recommended cross-client install path:

```bash
mkdir -p .agents/skills
cp -R /path/to/manim-video .agents/skills/manim-video
```

User-level cross-client install path:

```bash
mkdir -p ~/.agents/skills
cp -R /path/to/manim-video ~/.agents/skills/manim-video
```

Tool-specific paths:

```bash
# Claude Code, project-level
mkdir -p .claude/skills
cp -R /path/to/manim-video .claude/skills/manim-video

# Claude Code, personal
mkdir -p ~/.claude/skills
cp -R /path/to/manim-video ~/.claude/skills/manim-video

# Codex, personal
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R /path/to/manim-video "${CODEX_HOME:-$HOME/.codex}/skills/manim-video"
```

For Antigravity, OpenCode, VS Code/Copilot, Goose, Amp, and other Agent Skills-compatible tools, prefer `.agents/skills/manim-video/` when the tool scans it. If a tool uses its own skills directory, copy the same folder there. No content changes are needed.

Quick layout after project-level shared install:

```text
your-project/
  .agents/
    skills/
      manim-video/
        SKILL.md
        scripts/
        references/
```

## Setup

Install Docker Desktop or Docker Engine, then run:

macOS, Linux, WSL, or Git Bash:

```bash
cd /path/to/manim-video
bash scripts/setup.sh
```

Windows PowerShell:

```powershell
cd C:\path\to\manim-video
.\scripts\setup.ps1
```

The setup script checks Docker, builds `manim-video-runtime:v0.20.1` if needed, and verifies Manim, ffmpeg, and LaTeX inside the container.

## Render

From a Manim project directory:

macOS, Linux, WSL, or Git Bash:

```bash
/path/to/manim-video/scripts/manim.sh -ql script.py SceneName
```

Windows PowerShell:

```powershell
& "C:\path\to\manim-video\scripts\manim.ps1" -ql script.py SceneName
```

Production render:

```bash
/path/to/manim-video/scripts/manim.sh -qh script.py SceneName
```

Stitch scenes:

```bash
mkdir -p outputs
/path/to/manim-video/scripts/ffmpeg.sh -y -f concat -safe 0 -i concat.txt -c copy outputs/final.mp4
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force outputs
& "C:\path\to\manim-video\scripts\ffmpeg.ps1" -y -f concat -safe 0 -i concat.txt -c copy outputs/final.mp4
```

Useful overrides:

```bash
MANIM_DOCKER_IMAGE=your-custom-image /path/to/manim-video/scripts/manim.sh -ql script.py SceneName
MANIM_BASE_IMAGE=manimcommunity/manim:stable bash /path/to/manim-video/scripts/setup.sh --rebuild
MANIM_PROJECT_DIR=/path/to/project /path/to/manim-video/scripts/manim.sh -ql script.py SceneName
```

Windows PowerShell overrides:

```powershell
$env:MANIM_DOCKER_IMAGE = "your-custom-image"
& "C:\path\to\manim-video\scripts\manim.ps1" -ql script.py SceneName

$env:MANIM_BASE_IMAGE = "manimcommunity/manim:stable"
& "C:\path\to\manim-video\scripts\setup.ps1" -Rebuild

$env:MANIM_PROJECT_DIR = "C:\path\to\project"
& "C:\path\to\manim-video\scripts\manim.ps1" -ql script.py SceneName
```

## Smoke Test

macOS, Linux, WSL, or Git Bash:

```bash
mkdir -p /tmp/manim-smoke
cd /tmp/manim-smoke
cat > script.py <<'PY'
from manim import *

class HelloManim(Scene):
    def construct(self):
        self.camera.background_color = "#1C1C1C"
        title = Text("Manim works", font_size=48, color=BLUE)
        self.play(Write(title))
        self.wait(1)
PY

/path/to/manim-video/scripts/manim.sh -ql script.py HelloManim
```

Windows PowerShell:

```powershell
$SmokeDir = Join-Path $env:TEMP "manim-smoke"
mkdir $SmokeDir -Force
cd $SmokeDir
@'
from manim import *

class HelloManim(Scene):
    def construct(self):
        self.camera.background_color = "#1C1C1C"
        title = Text("Manim works", font_size=48, color=BLUE)
        self.play(Write(title))
        self.wait(1)
'@ | Set-Content script.py

& "C:\path\to\manim-video\scripts\manim.ps1" -ql script.py HelloManim
```

The output appears under `media/videos/script/480p15/HelloManim.mp4`.

## Output Hygiene

The Docker wrappers remove the container after each run, but files written inside `/manim` are written to the local project directory and persist. Manim writes draft scene renders and caches under `media/`; ffmpeg writes wherever the output path points.

Recommended convention:

- Keep final/shareable files under `outputs/`, such as `outputs/final.mp4`.
- For single-scene renders, copy the accepted Manim render from `media/videos/...` into `outputs/` before handoff.
- Treat `media/` as generated render output/cache, not the canonical final location; it can be deleted and regenerated.
- Treat `review-frames/`, `concat.txt`, and `audio_concat.txt` as temporary review/stitching artifacts. Clear `review-frames/` before new frame extraction and delete it after final review.
- Avoid copying final videos into hidden tool-specific cache folders unless the host UI requires an embedded artifact. If a tool creates that secondary copy, keep `outputs/` as the primary project-local location.
- Keep `script.py`, `plan.md`, source assets, narration audio, and approved files under `outputs/`.

## Notes

- The default runtime image is `manim-video-runtime:v0.20.1`, built from `manimcommunity/manim:v0.20.1` plus ffmpeg for reproducible open-source support.
- Set `MANIM_BASE_IMAGE=manimcommunity/manim:stable` and run `scripts/setup.sh --rebuild` or `scripts\setup.ps1 -Rebuild` to rebuild the local runtime from the latest Manim release.
- Set `MANIM_DOCKER_IMAGE=your-custom-image` to skip the local image and use a fully custom runtime.
- Supported host path is intentionally small: Docker Desktop/Engine plus Bash or PowerShell. Python, Manim, LaTeX, and ffmpeg do not need host installs.
- Docker preview/file-browser flags such as `-p` and `-f` are not useful inside the container.
- The official Manim base includes TeX Live but not a standalone ffmpeg binary, so this skill's Dockerfile installs ffmpeg. For extra LaTeX packages or Python plugins, extend the Dockerfile or set `MANIM_DOCKER_IMAGE`.

Official Docker docs: https://docs.manim.community/en/stable/installation/docker.html
