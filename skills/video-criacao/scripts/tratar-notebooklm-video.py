#!/usr/bin/env python3
"""Script de pós-produção para vídeos do Gemini Notebook / NotebookLM.

Remove a marca d'água no canto inferior direito (delogo/crop/overlay)
e corta a tela de encerramento com a logo final do Google/NotebookLM,
além de normalizar áudio para -14 LUFS e aplicar +faststart.

Uso:
    python3 tratar-notebooklm-video.py <input.mp4> <output.mp4>
"""

import sys
import os
import subprocess
import json
from pathlib import Path

def process_video(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Erro: arquivo de entrada não encontrado: {input_path}")
        sys.exit(1)

    # 1. Obter duração total do vídeo
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", input_path
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    duration = float(json.loads(res.stdout)["format"]["duration"])
    
    # Cortar os últimos 3.5 segundos (tela de encerramento da logo)
    target_duration = max(0, duration - 3.5)
    print(f"[1/3] Duração original: {duration:.2f}s -> Cortando encerramento para: {target_duration:.2f}s")

    # 2. Aplicar filtro delogo no canto inferior direito
    # Coordenadas típicas do logo NotebookLM em 1280x720: x=1060, y=660, w=200, h=50
    # E normalizar áudio para padrão de broadcast YouTube (-14 LUFS)
    filter_complex = (
        f"[0:v]delogo=x=1050:y=655:w=220:h=55:show=0[vclean]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", "0",
        "-t", str(target_duration),
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[vclean]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-af", "loudnorm=I=-14.0:TP=-1.5:LRA=7.0",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ]
    
    print(f"[2/3] Executando pipeline FFmpeg (delogo + trim + loudnorm)...")
    subprocess.run(cmd, check=True)
    print(f"[3/3] Sucesso! Vídeo limpo e normalizado salvo em: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 tratar-notebooklm-video.py <input.mp4> <output.mp4>")
        sys.exit(1)
    process_video(sys.argv[1], sys.argv[2])
