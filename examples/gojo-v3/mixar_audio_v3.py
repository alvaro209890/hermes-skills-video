#!/usr/bin/env python3
"""Mix v3: sidechain mais musical, ambience vocal e loudnorm em dois passes."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIR = ROOT / "voz_v3"
BEAT = DIR / "beat.wav"
VOCALS = DIR / "vocals.wav"
PRE = DIR / "mix_pre.wav"
LOUD = DIR / "mix_loud.wav"
OUT = DIR / "mix.wav"
DURATION = 30.0


def run(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=capture)


def main() -> None:
    filt = (
        f"[1:a]atrim=0:{DURATION:.2f},apad=pad_dur=0.1,atrim=0:{DURATION:.2f},"
        "asplit=4[sc][dry][verb][slap];"
        "[0:a]volume=0.66[beat];"
        "[beat][sc]sidechaincompress=threshold=0.020:ratio=9.5:attack=3:release=135:makeup=1[duck];"
        "[dry]volume=1.08[voc];"
        "[verb]highpass=f=190,lowpass=f=7600,"
        "aecho=0.80:0.68:84|168|252:0.12|0.065|0.035,volume=0.25[space];"
        "[slap]highpass=f=250,lowpass=f=5600,adelay=64|91,volume=0.085[sl];"
        "[duck][voc][space][sl]amix=inputs=4:weights='1 1 1 1':normalize=0,"
        "asoftclip=type=tanh:threshold=0.95:output=0.96:oversample=4,"
        "alimiter=limit=0.965:attack=2:release=50[mix]"
    )
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(BEAT), "-i", str(VOCALS),
        "-filter_complex", filt, "-map", "[mix]", "-t", f"{DURATION:.2f}",
        "-ar", "48000", "-c:a", "pcm_s24le", str(PRE),
    ])

    first = run([
        "ffmpeg", "-hide_banner", "-i", str(PRE),
        "-af", "loudnorm=I=-12:TP=-1.5:LRA=5:print_format=json", "-f", "null", "-",
    ], capture=True)
    match = re.search(r"\{\s*\"input_i\".*?\}", first.stderr, re.S)
    if not match:
        raise RuntimeError("medidas loudnorm ausentes")
    m = json.loads(match.group(0))
    second = (
        "loudnorm=I=-12:TP=-1.5:LRA=5:"
        f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
        f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
        f"offset={m['target_offset']}:linear=true:print_format=summary"
    )
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(PRE), "-af", second,
        "-ar", "48000", "-c:a", "pcm_s24le", str(LOUD),
    ])
    # AAC pode criar picos interamostra muito acima do WAV. Limitador 4x a
    # -4,44 dBFS + ganho medido preserva ~-12 LUFS e chega ao AAC abaixo de -1 dBTP.
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(LOUD),
        "-af", (
            "aresample=192000,"
            "alimiter=limit=0.60:attack=5:release=80:level=false,"
            "volume=0.7dB,aresample=48000"
        ),
        "-ar", "48000", "-c:a", "pcm_s24le", str(OUT),
    ])
    print(
        f"ok: {OUT} | entrada {m['input_i']} LUFS / {m['input_tp']} dBTP "
        "-> premaster -12 LUFS / -1.5 dBTP + proteção AAC 4x"
    )


if __name__ == "__main__":
    main()
