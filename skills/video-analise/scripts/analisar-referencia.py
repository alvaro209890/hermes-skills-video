#!/usr/bin/env python3
"""Mede ritmo de corte, pulso e loudness de uma referência com FFmpeg + NumPy."""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import statistics
import subprocess
import wave
from pathlib import Path

import numpy as np


def run(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=capture)


def probe(path: Path) -> dict:
    p = run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path),
    ], capture=True)
    return json.loads(p.stdout)


def media_info(data: dict) -> tuple[float, str, str, str]:
    duration = float(data.get("format", {}).get("duration", 0) or 0)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    resolution = f"{video.get('width', '?')}x{video.get('height', '?')}"
    fps = video.get("avg_frame_rate", video.get("r_frame_rate", "?"))
    audio_desc = f"{audio.get('codec_name', 'sem áudio')} / {audio.get('sample_rate', '?')} Hz"
    return duration, resolution, fps, audio_desc


def extract_audio(source: Path, out: Path, seconds: float) -> bool:
    p = subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(source), "-t", f"{seconds:.3f}",
        "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(out),
    ])
    return p.returncode == 0 and out.exists()


def estimate_bpm(audio: Path) -> tuple[float, float]:
    with wave.open(str(audio), "rb") as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.0
    hop = max(1, round(sr * 0.01))
    x = x[: len(x) // hop * hop]
    if len(x) < hop * 500:
        return 0.0, 0.0
    rms = np.sqrt(np.mean(x.reshape(-1, hop) ** 2, axis=1) + 1e-12)
    onset = np.maximum(0.0, np.diff(rms, prepend=rms[0]))
    onset -= np.mean(onset)
    onset /= np.std(onset) + 1e-9
    best_bpm, best_score = 0.0, -1e9
    for bpm in np.linspace(70.0, 200.0, 1301):
        lag = max(1, round(60.0 / bpm / 0.01))
        score = float(np.dot(onset[lag:], onset[:-lag]) / max(1, len(onset) - lag))
        # Favorece BPM musical central sem impedir half/double-time.
        score *= 0.97 + 0.03 * math.exp(-((bpm - 115) / 55) ** 2)
        if score > best_score:
            best_bpm, best_score = float(bpm), score
    return best_bpm, best_score


def scene_metrics(source: Path, metadata: Path, seconds: float, threshold: float) -> tuple[list[float], list[float]]:
    # O writer `metadata=print` pode preservar conteúdo de execução anterior.
    # Remover só este artefato gerado evita misturar timestamps de janelas distintas.
    metadata.unlink(missing_ok=True)
    safe_meta = str(metadata).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(source),
        "-vf", (
            f"trim=start=0:end={seconds:.6f},setpts=PTS-STARTPTS,"
            f"select='gt(scene,{threshold:.3f})',metadata=print:file='{safe_meta}'"
        ),
        "-an", "-f", "null", "-",
    ])
    raw = metadata.read_text(encoding="utf-8", errors="replace") if metadata.exists() else ""
    raw_times = [float(v) for v in re.findall(r"pts_time:([0-9.]+)", raw)]
    times: list[float] = []
    for value in raw_times:
        if value <= seconds + 0.05 and (not times or value - times[-1] >= 0.08):
            times.append(value)
    boundaries = [0.0, *times, seconds]
    intervals = [b - a for a, b in zip(boundaries, boundaries[1:]) if b > a]
    return times, intervals


def loudness(source: Path, seconds: float) -> tuple[str, str, str]:
    p = subprocess.run([
        "ffmpeg", "-hide_banner", "-i", str(source), "-t", f"{seconds:.3f}",
        "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-",
    ], text=True, capture_output=True)
    values_i = re.findall(r"I:\s+(-?inf|-?[0-9.]+) LUFS", p.stderr)
    values_lra = re.findall(r"LRA:\s+([0-9.]+) LU", p.stderr)
    values_peak = re.findall(r"Peak:\s+(-?inf|-?[0-9.]+) dBFS", p.stderr)
    return (
        values_i[-1] if values_i else "n/d",
        values_lra[-1] if values_lra else "n/d",
        values_peak[-1] if values_peak else "n/d",
    )


def contact_sheet(source: Path, out: Path, seconds: float) -> None:
    fps = 15.0 / max(seconds, 0.5)
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(source), "-t", f"{seconds:.3f}",
        "-vf", f"fps={fps:.9f},scale=320:-2,tile=5x3", "-frames:v", "1", "-q:v", "2", str(out),
    ])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", type=Path)
    ap.add_argument("saida", type=Path)
    ap.add_argument("--segundos", type=float, default=35.0)
    ap.add_argument("--scene-threshold", type=float, default=0.18)
    args = ap.parse_args()
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            raise SystemExit(f"ferramenta ausente: {tool}")
    if not args.video.is_file():
        raise SystemExit(f"vídeo não encontrado: {args.video}")
    args.saida.mkdir(parents=True, exist_ok=True)

    data = probe(args.video)
    duration, resolution, fps, audio_desc = media_info(data)
    seconds = min(max(0.5, args.segundos), duration) if duration else max(0.5, args.segundos)
    metadata = args.saida / "cortes_metadata.txt"
    times, intervals = scene_metrics(args.video, metadata, seconds, args.scene_threshold)
    contact = args.saida / "contato_15.jpg"
    contact_sheet(args.video, contact, seconds)

    audio = args.saida / "audio_analise.wav"
    if extract_audio(args.video, audio, seconds):
        bpm, confidence = estimate_bpm(audio)
        integrated, lra, peak = loudness(args.video, seconds)
    else:
        bpm = confidence = 0.0
        integrated = lra = peak = "n/d"

    changes_per_10 = len(times) / seconds * 10.0
    median_shot = statistics.median(intervals) if intervals else seconds
    mean_shot = statistics.mean(intervals) if intervals else seconds
    alt = bpm / 2 if bpm >= 135 else bpm * 2 if bpm and bpm < 100 else 0.0
    timestamps = ", ".join(f"{t:.2f}s" for t in times[:40]) or "nenhum"
    report = f"""# Análise técnica da referência

- Fonte: `{args.video}`
- Janela medida: {seconds:.3f} s de {duration:.3f} s
- Vídeo: {resolution}, {fps} fps
- Áudio: {audio_desc}

## Ritmo visual

- Mudanças com `scene>{args.scene_threshold:.2f}`: {len(times)}
- Densidade: {changes_per_10:.2f} eventos/10 s
- Plano mediano: {median_shot:.3f} s
- Plano médio: {mean_shot:.3f} s
- Timestamps: {timestamps}

## Ritmo e áudio

- BPM estimado por autocorrelação de onsets: {bpm:.1f}
- Leitura half/double-time plausível: {alt:.1f}
- Score relativo do pulso: {confidence:.3f}
- Loudness integrado: {integrated} LUFS
- LRA: {lra} LU
- True peak: {peak} dBFS

## Artefatos

- Folha de contato: `{contact.name}`
- Eventos brutos: `{metadata.name}`
- Áudio mono de medição: `{audio.name}`

Os números descrevem a janela; cor, composição, voz e transições ainda exigem inspeção humana dos quadros e escuta.
"""
    (args.saida / "ANALISE_TECNICA.md").write_text(report, encoding="utf-8")
    print(json.dumps({
        "duracao_analisada": round(seconds, 3),
        "mudancas": len(times),
        "eventos_por_10s": round(changes_per_10, 2),
        "plano_mediano_s": round(median_shot, 3),
        "bpm": round(bpm, 1),
        "lufs_i": integrated,
        "lra": lra,
        "true_peak": peak,
        "relatorio": str(args.saida / "ANALISE_TECNICA.md"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
