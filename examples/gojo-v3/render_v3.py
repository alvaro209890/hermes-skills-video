#!/usr/bin/env python3
"""Render vertical v3: grade de 95 BPM, microtransições e legenda cinética."""

from __future__ import annotations

import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PANEL_DIR = ROOT / "assets_v3" / "paineis"
CLIP_DIR = ROOT / "clips_v3"
MIX = ROOT / "voz_v3" / "mix.wav"
ASS = ROOT / "legenda_v3.ass"
OUT = ROOT.parent.parent / "saidas" / "gojo_15s_v3.mp4"
FPS = 30
BPM = 95.0
BEAT = 60.0 / BPM
STEP = 2 * BEAT
FRAMES = 42
CLIP_DUR = FRAMES / FPS
XFADE = CLIP_DUR - STEP
DURATION = 30.0
TRANSITIONS = [
    "fadeblack", "wipeleft", "dissolve", "smoothup", "slideleft", "fade",
    "circleopen", "wipeleft", "fadeblack", "smoothleft", "dissolve", "wiperight",
    "fade", "slideup", "circleopen", "wipeleft", "fadeblack", "smoothup",
    "dissolve", "slideleft", "fade", "wiperight", "fadeblack",
]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def make_clip(item: tuple[int, Path]) -> Path:
    index, image = item
    out = CLIP_DIR / f"clip_{index:02d}.mp4"
    if out.exists() and out.stat().st_mtime >= image.stat().st_mtime:
        return out
    impact = index in {2, 7, 12, 17, 19, 22}
    if impact:
        vf = (
            "scale=1140:2027:force_original_aspect_ratio=increase,"
            "crop=1080:1920:x='30+12*sin(n*2.4)':y='53+10*cos(n*2.8)',"
            "eq=contrast=1.10:saturation=1.18,unsharp=5:5:0.55,format=yuv420p"
        )
    elif index % 3 == 0:
        vf = (
            "scale=1320:2347,"
            "zoompan=z='min(zoom+0.0022,1.112)':"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={FRAMES}:s=1080x1920:fps={FPS},"
            "eq=contrast=1.055:saturation=1.10,unsharp=5:5:0.38,format=yuv420p"
        )
    elif index % 3 == 1:
        vf = (
            "scale=1320:2347,"
            "zoompan=z='1.075':x='(iw-iw/zoom)*(on/41)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={FRAMES}:s=1080x1920:fps={FPS},"
            "eq=contrast=1.055:saturation=1.10,unsharp=5:5:0.38,format=yuv420p"
        )
    else:
        vf = (
            "scale=1320:2347,"
            "zoompan=z='if(eq(on,1),1.11,max(zoom-0.0021,1.02))':"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={FRAMES}:s=1080x1920:fps={FPS},"
            "eq=contrast=1.055:saturation=1.10,unsharp=5:5:0.38,format=yuv420p"
        )
    run([
        "ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(image),
        "-vf", vf, "-frames:v", str(FRAMES), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an", str(out),
    ])
    return out


def render(clips: list[Path]) -> None:
    cmd = ["ffmpeg", "-y", "-v", "warning"]
    for clip in clips:
        cmd += ["-i", str(clip)]
    cmd += ["-i", str(MIX)]
    filters: list[str] = []
    previous = "0:v"
    for i in range(1, len(clips)):
        label = f"x{i}"
        filters.append(
            f"[{previous}][{i}:v]xfade=transition={TRANSITIONS[i - 1]}:"
            f"duration={XFADE:.6f}:offset={i * STEP:.6f}[{label}]"
        )
        previous = label

    # Microimpactos de 60–75 ms nas oito entradas da voz, sempre sobre a grade.
    starts = [BEAT * (4 + 5 * i) for i in range(8)]
    flashes = "+".join(f"between(t,{t:.6f},{t + 0.068:.6f})" for t in starts)
    purple = "+".join(f"between(t,{t:.6f},{t + 0.050:.6f})" for t in (starts[2], starts[4], starts[6]))
    ass_path = str(ASS).replace("'", r"\'")
    filters.append(
        f"[{previous}]drawbox=x=0:y=0:w=iw:h=ih:color=white@0.30:t=fill:enable='{flashes}',"
        f"drawbox=x=0:y=0:w=iw:h=ih:color=0x9B35FF@0.26:t=fill:enable='{purple}',"
        f"ass=filename='{ass_path}',format=yuv420p[vout]"
    )
    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", f"{len(clips)}:a:0", "-t", f"{DURATION:.3f}",
        "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(OUT),
    ]
    run(cmd)


def main() -> None:
    panels = sorted(PANEL_DIR.glob("painel_*.png"))
    missing = [p for p in (MIX, ASS) if not p.exists()]
    if len(panels) != 24 or missing:
        raise SystemExit(f"Esperados 24 painéis e áudio/ASS; painéis={len(panels)}, ausentes={missing}")
    CLIP_DIR.mkdir(exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        clips = list(pool.map(make_clip, enumerate(panels)))
    print(f"montagem: 24 planos, passo={STEP:.6f}s, xfade={XFADE:.6f}s", flush=True)
    render(clips)
    print(f"ok: {OUT}", flush=True)


if __name__ == "__main__":
    main()
