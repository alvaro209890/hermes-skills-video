#!/usr/bin/env python3
"""Voz rap v3: Edge em 48 kHz, Rubber Band e formante preservado."""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "voz_v3"
SR = 48_000
VOICE = os.environ.get("GOJO_EDGE_VOICE", "en-US-AndrewMultilingualNeural")
EDGE_RATE = os.environ.get("GOJO_EDGE_RATE", "+15%")
PITCH_ST = float(os.environ.get("GOJO_PITCH_ST", "-1.5"))
PITCH = 2 ** (PITCH_ST / 12.0)
REUSE_RAW = os.environ.get("GOJO_REUSE_RAW", "0") == "1"

# Pontuacao pensada para fala; nenhuma palavra da letra aprovada foi alterada.
SPEECH = [
    "Seis olhos abertos, eu enxergo o que ninguém vê.",
    "O infinito na minha frente, cê chega mas não me alcança.",
    "Roxo vazio na palma, mais e menos colidem.",
    "E o silêncio depois do estouro é a única herança.",
    "Eu sou o mais forte, não é vaidade, é sentença.",
    "Sozinho no topo, porque o topo não tem companhia.",
    "Gojo Satoru, o limite virou lembrança.",
    "Acima do infinito ainda cabe mais um dia.",
]

CAPTIONS = [
    "SEIS OLHOS ABERTOS, EU ENXERGO O QUE NINGUÉM VÊ",
    "O INFINITO NA MINHA FRENTE: CÊ CHEGA, MAS NÃO ME ALCANÇA",
    "ROXO VAZIO NA PALMA, MAIS E MENOS COLIDEM",
    "E O SILÊNCIO DEPOIS DO ESTOURO É A ÚNICA HERANÇA",
    "EU SOU O MAIS FORTE. NÃO É VAIDADE, É SENTENÇA",
    "SOZINHO NO TOPO, PORQUE O TOPO NÃO TEM COMPANHIA",
    "GOJO SATORU: O LIMITE VIROU LEMBRANÇA",
    "ACIMA DO INFINITO AINDA CABE MAIS UM DIA",
]

IMPACTS = [
    "SEIS OLHOS", "INFINITO", "ROXO VAZIO", "SILÊNCIO",
    "MAIS FORTE", "SOZINHO NO TOPO", "GOJO SATORU", "ACIMA DO INFINITO",
]

# Grade validada nos quatro modelos: 95 BPM, entrada apos quatro tempos,
# nova barra vocal a cada cinco tempos e tomada maxima de 4,75 tempos.
BPM = 95.0
BEAT = 60.0 / BPM
STARTS = [BEAT * (4 + 5 * i) for i in range(8)]
ENDS = [s + BEAT * 4.75 for s in STARTS]


def run(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=capture)


def duration(path: Path) -> float:
    p = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(path),
    ], capture=True)
    return float(p.stdout.strip())


def synthesize() -> list[Path]:
    raws: list[Path] = []
    for i, text in enumerate(SPEECH, 1):
        mp3 = OUT / f"l{i:02d}_raw.mp3"
        if not (REUSE_RAW and mp3.exists()):
            run([
                "edge-tts", "--voice", VOICE, "--rate", EDGE_RATE, "--pitch", "+0Hz",
                "--text", text, "--write-media", str(mp3),
            ])
        trimmed = OUT / f"l{i:02d}_trim.wav"
        run([
            "ffmpeg", "-y", "-v", "error", "-i", str(mp3),
            "-af", (
                "aresample=48000,"
                "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-48dB:"
                "start_silence=0.015,areverse,"
                "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-48dB:"
                "start_silence=0.030,areverse"
            ),
            "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(trimmed),
        ])
        raws.append(trimmed)
    return raws


def process(raws: list[Path]) -> list[Path]:
    results: list[Path] = []
    for i, raw in enumerate(raws):
        target = ENDS[i] - STARTS[i]
        raw_dur = duration(raw)
        # Nunca desacelerar TTS curto: isso alonga vogais e denuncia o sintetizador.
        # Acelerar apenas quando a tomada realmente ultrapassa o slot; completar o resto com pausa.
        tempo = max(1.0, raw_dur / target)
        if tempo > 1.15:
            raise RuntimeError(
                f"linha {i + 1} exige {tempo:.3f}x (>1.15x); regenere ou ajuste a prosodia"
            )
        out = OUT / f"l{i + 1:02d}_rap.wav"
        filt = ",".join([
            "aresample=48000",
            (
                f"rubberband=tempo={tempo:.8f}:pitch={PITCH:.8f}:"
                "transients=smooth:detector=soft:phase=laminar:window=long:"
                "smoothing=on:formant=preserved:pitchq=quality:channels=together"
            ),
            "highpass=f=68",
            "lowpass=f=11800",
            "equalizer=f=170:t=q:w=1.05:g=2.6",
            "equalizer=f=300:t=q:w=1.15:g=1.2",
            "equalizer=f=520:t=q:w=1.1:g=-1.2",
            "equalizer=f=2550:t=q:w=1.0:g=1.8",
            "equalizer=f=7100:t=q:w=1.1:g=-1.8",
            "deesser=i=0.18:m=0.45:f=0.30",
            "acompressor=threshold=0.095:ratio=3.6:attack=7:release=95:makeup=1.85:knee=2.8",
            "asoftclip=type=tanh:threshold=0.92:output=0.95:oversample=4",
            f"apad=pad_dur={target:.4f}",
            f"atrim=0:{target:.4f}",
            "asetpts=PTS-STARTPTS",
        ])
        run([
            "ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", filt,
            "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(out),
        ])
        print(f"linha {i + 1}: {raw_dur:.3f}s -> {target:.3f}s (tempo {tempo:.3f}x)")
        results.append(out)
    return results


def read_mono(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (SR, 1, 2):
            raise ValueError(f"WAV inesperado: {path}")
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.0


def assemble(lines: list[Path]) -> Path:
    audio = np.zeros(round(30.0 * SR), np.float64)
    for start, line in zip(STARTS, lines):
        x = read_mono(line)
        pos = round(start * SR)
        end = min(len(audio), pos + len(x))
        audio[pos:end] += x[: end - pos]
    peak = np.max(np.abs(audio))
    if peak > 0.95:
        audio *= 0.95 / peak
    out = OUT / "lead_mono.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
    return out


def stereo_voice(lead: Path) -> Path:
    out = OUT / "vocals.wav"
    filt = (
        "[0:a]asplit=5[main][dl][dr][harm][air];"
        "[main]pan=stereo|c0=0.96*c0|c1=0.96*c0[m];"
        "[dl]rubberband=pitch=0.992:formant=preserved:pitchq=quality,"
        "highpass=f=130,lowpass=f=6800,adelay=18,volume=0.125,"
        "pan=stereo|c0=c0|c1=0*c0[l];"
        "[dr]rubberband=pitch=1.008:formant=preserved:pitchq=quality,"
        "highpass=f=130,lowpass=f=6400,adelay=31,volume=0.105,"
        "pan=stereo|c0=0*c0|c1=c0[r];"
        "[harm]rubberband=pitch=0.749154:formant=preserved:pitchq=quality,"
        "highpass=f=110,lowpass=f=4200,volume=0.065:enable='between(t,15,27)',"
        "pan=stereo|c0=0.7*c0|c1=0.7*c0[h];"
        "[air]highpass=f=3200,lowpass=f=11000,deesser=i=0.18:m=0.45:f=0.62,"
        "volume=0.055,pan=stereo|c0=c0|c1=c0[a];"
        "[m][l][r][h][a]amix=inputs=5:normalize=0,"
        "asoftclip=type=tanh:threshold=0.96:output=0.96:oversample=4[out]"
    )
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(lead),
        "-filter_complex", filt, "-map", "[out]", "-ar", str(SR),
        "-c:a", "pcm_s16le", str(out),
    ])
    return out


def ass_time(seconds: float) -> str:
    cs = round(seconds * 100)
    return f"{cs // 360000}:{(cs // 6000) % 60:02d}:{(cs // 100) % 60:02d}.{cs % 100:02d}"


def wrap_balanced(text: str) -> str:
    words = text.split()
    if len(text) <= 29:
        return text
    cut = min(
        range(1, len(words)),
        key=lambda n: abs(len(" ".join(words[:n])) - len(" ".join(words[n:]))),
    )
    return " ".join(words[:cut]) + r"\N" + " ".join(words[cut:])


def karaoke(text: str, seconds: float) -> str:
    words = text.split()
    weights = [max(2, len(w.replace(r"\N", "").strip(".,:!?"))) for w in words]
    total = round(seconds * 100)
    spans = [max(1, round(total * w / sum(weights))) for w in weights]
    spans[-1] += total - sum(spans)
    return " ".join(f"{{\\kf{span}}}{word}" for span, word in zip(spans, words))


def write_subtitles() -> None:
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: RapBlue,DejaVu Sans,52,&H00FFFFFF,&H00FFF060,&H00120B18,&H68000000,-1,0,0,0,100,100,1,0,1,4,2,2,92,92,500,1
Style: RapPurple,DejaVu Sans,52,&H00FFFFFF,&H00F69AF2,&H00120B18,&H68000000,-1,0,0,0,100,100,1,0,1,4,2,2,92,92,500,1
Style: Impact,DejaVu Sans,94,&H00FFFFFF,&H00FFFFFF,&H008625D0,&H30000000,-1,0,0,0,100,100,2,0,1,6,3,5,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    rows: list[str] = []
    timings = []
    for i, (start, end, caption, impact) in enumerate(zip(STARTS, ENDS, CAPTIONS, IMPACTS)):
        style = "RapBlue" if i < 4 else "RapPurple"
        wrapped = wrap_balanced(caption)
        rows.append(
            f"Dialogue: 1,{ass_time(start)},{ass_time(end)},{style},,0,0,0,,"
            r"{\fad(60,90)\blur0.25}" + karaoke(wrapped, end - start)
        )
        impact_end = min(end, start + 0.72)
        impact_color = "&H00FFF060&" if i < 4 else "&H00F69AF2&"
        rows.append(
            f"Dialogue: 0,{ass_time(start)},{ass_time(impact_end)},Impact,,0,0,0,,"
            rf"{{\an5\pos(540,820)\c{impact_color}\fscx118\fscy118"
            rf"\t(0,260,\fscx100\fscy100)\fad(40,120)}}{impact}"
        )
        timings.append({"start": start, "end": end, "text": caption, "impact": impact})
    (ROOT / "legenda_v3.ass").write_text(header + "\n".join(rows) + "\n", encoding="utf-8")
    (ROOT / "timings_v3.json").write_text(
        json.dumps(timings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    for tool in ("edge-tts", "ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            raise SystemExit(f"Ferramenta ausente: {tool}")
    filters = run(["ffmpeg", "-hide_banner", "-filters"], capture=True)
    if "rubberband" not in filters.stdout:
        raise SystemExit("ffmpeg sem filtro rubberband")
    OUT.mkdir(exist_ok=True)
    raws = synthesize()
    lines = process(raws)
    lead = assemble(lines)
    vocals = stereo_voice(lead)
    write_subtitles()
    print(
        f"ok: {vocals} ({duration(vocals):.3f}s), voz={VOICE}, "
        f"edge={EDGE_RATE}, pitch={PITCH_ST:+.1f} st"
    )


if __name__ == "__main__":
    main()
