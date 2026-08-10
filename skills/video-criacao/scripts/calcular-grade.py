#!/usr/bin/env python3
"""Calcula cortes e microimpactos musicais sem arredondar a grade."""

from __future__ import annotations

import argparse
import json


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bpm", type=float)
    ap.add_argument("duracao", type=float)
    ap.add_argument("--beats-por-plano", type=float, default=2.0)
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--frames-por-clip", type=int, default=42)
    args = ap.parse_args()
    if (
        args.bpm <= 0
        or args.duracao <= 0
        or args.beats_por_plano <= 0
        or args.fps <= 0
        or args.frames_por_clip <= 0
    ):
        raise SystemExit("valores devem ser positivos")
    beat = 60.0 / args.bpm
    step = beat * args.beats_por_plano
    clip = args.frames_por_clip / args.fps
    xfade = clip - step
    if xfade < 0:
        raise SystemExit(f"clip curto: {clip:.6f}s < passo {step:.6f}s")
    cuts = []
    t = 0.0
    while t < args.duracao:
        cuts.append(round(t, 6))
        t += step
    print(json.dumps({
        "bpm": args.bpm,
        "beat_s": round(beat, 9),
        "microimpacto_meio_beat_s": round(beat / 2, 9),
        "passo_plano_s": round(step, 9),
        "clip_s": round(clip, 9),
        "xfade_s": round(xfade, 9),
        "quantidade_planos": len(cuts),
        "offsets_s": cuts,
    }, indent=2))


if __name__ == "__main__":
    main()
