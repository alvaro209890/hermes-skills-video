# Rap BR v3 — calibração RM RAPS e comandos reproduzíveis

Validado em 2026-08-10 no clipe Gojo v3, usando como linguagem de referência quatro vídeos
oficiais do RM RAPS: Gojo, Mahoraga, Toji e Hajime Kashimo. Os arquivos protegidos serviram
apenas para análise local e não entram no repositório.

## O que foi medido

| Modelo | Pulso útil | Eventos visuais/10 s | Linguagem aproveitada |
|---|---:|---:|---|
| Gojo | ~95/190 BPM | 6,6 | azul/violeta, impacto e close |
| Mahoraga | ~70/140 BPM | 6,9 | preto/verde-petróleo, vermelho e peso |
| Toji | ~90/180 BPM | 6,6 | sépia/vermelho, quadros de mangá |
| Kashimo | ~95/190 BPM | 9,1 | ciano, relâmpago, glitch e espaço negativo |

Grade escolhida para 95 BPM:

- beat: `0.631578947 s`;
- microimpacto: `0.315789474 s`;
- plano-base de 2 beats: `1.263157895 s`;
- respiro de 4 beats: `2.526315789 s`.

Calcular sem arredondar manualmente:

```bash
scripts/calcular-grade.py 95 30 --beats-por-plano 2 --fps 30 --frames-por-clip 42
```

Com clips de 42 frames (`1,4 s`), o microxfade é `0.136842105 s` e o offset `i×1.263157895`.

## Voz vencedora

Comparação local de Antônio, Andrew Multilingual e Brian:

- `en-US-AndrewMultilingualNeural`, `+15%`, pitch −1,5 st;
- F0 mediana 122 Hz; 65,4% da energia entre 80–350 Hz;
- presença 2–5 kHz: 12%; sibilância 6–8 kHz: 0,35%;
- nas oito linhas, maior aceleração necessária: 1,064× após trim de bordas.

```bash
edge-tts --voice en-US-AndrewMultilingualNeural --rate='+15%' --pitch='+0Hz' \
  --text 'Seis olhos abertos, eu enxergo o que ninguém vê.' \
  --write-media linha_raw.mp3

scripts/processar-voz-rap.sh linha_raw.mp3 linha_rap.wav -1.5 1.0
```

O script usa:

```text
aresample 48 kHz
→ trim só nas bordas
→ rubberband pitch=0.917004 tempo≤1.15 formant=preserved
→ HPF/LPF + EQ 170/300/520/2550/7100 Hz
→ de-esser + compressor 3.6:1 + softclip
→ double filtrado 18/31 ms
```

### Bug proibido

Não aplicar `asetrate=48000*fator` diretamente a MP3 Edge sem resample. Edge decodifica
normalmente a 24 kHz; assumir 48 kHz encurtou uma linha de 3,552 s para 1,364 s na v2,
criando a voz “metralhadora”. Rubber Band evita essa ambiguidade e preserva formante.

Também não usar `silenceremove=stop_periods=-1`: ele apaga pausas internas, parte do flow.

## Beat e mix

- Kick com corpo e 808/sub simples; clap/snare nos tempos 2 e 4; hats em 1/16.
- Sidechain: voz como chave, `ratio≈9.5`, ataque 3 ms, release 135 ms, ducking audível 2–4 dB.
- Lead mono no centro; doubles discretos entre −18 e −20 dB.
- Master curto: −13 a −11 LUFS-I; medir **o AAC decodificado**, não só o WAV.

```bash
ffmpeg -i beat.wav -i vocals.wav -filter_complex \
  "[1:a]asplit=2[sc][v];[0:a][sc]sidechaincompress=threshold=0.020:ratio=9.5:attack=3:release=135[b];[b][v]amix=2:normalize=0[m]" \
  -map '[m]' -ar 48000 mix_pre.wav
```

Depois do `loudnorm`, deixar margem e usar limiter em oversampling antes do AAC quando o
codec criar picos interamostra:

```bash
ffmpeg -i mix_loud.wav -af \
  "aresample=192000,alimiter=limit=0.60:attack=5:release=80:level=false,volume=0.7dB,aresample=48000" \
  -c:a pcm_s24le mix.wav
```

## Visual e QA

- Corte/base a cada dois beats; transições de ~4 frames.
- Microflash nas entradas vocais; tremor só em impactos.
- Três atos visuais podem reutilizar a linguagem dos modelos, não seus quadros.
- ASS vem dos timings da voz processada; safe area 9:16: x 100–860, y 300–1450.
- Obrigatório: decode completo, ffprobe, contato de frames, LUFS/LRA/TP do MP4 e faststart.

```bash
scripts/validar-export.sh final.mp4
```
