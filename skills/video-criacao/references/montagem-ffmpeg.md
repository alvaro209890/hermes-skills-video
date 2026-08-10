# Montagem de clipe com ffmpeg — receitas v1/v2 VALIDADAS (2026-08-10)

> Para a cadeia v3 (Andrew Multilingual, Rubber Band, grade 95 BPM, três linguagens
> visuais e proteção de true peak pós-AAC), leia também `rap-v3-modelos.md`.

Executada de ponta a ponta no clipe "GOJO — ACIMA DO INFINITO"
(`~/Documentos/Video_Studio/projetos/gojo-15s/` → `saidas/gojo_15s.mp4`, 25.2s, 1080×1920,
~18MB, entregue no WhatsApp). A etapa de render que o plano marcava ⛔ FUNCIONA com esta receita
— todo o resto do pipeline (letra → TTS → batida → cenas) também foi validado na prática.

## Estrutura de trabalho (padrão do Video_Studio)

```
~/Documentos/Video_Studio/
├── entradas/<slug>/          # downloads yt-dlp + keyframes (baixar-video.sh)
├── projetos/<slug>/          # assets/ (cenas .png), voz/ (TTS + beat + mix), scripts
└── saidas/                   # MP4 final + letra.txt + build.sh
```

## 1. Clips por cena com zoompan (Ken Burns)

Uma imagem 1080×1920 por cena; duração `d` por cena. **Upscale 1.25x ANTES** do zoompan
(scale=1350:2400) para o zoom não revelar pixel.

```bash
# zoom IN:  z='min(zoom+0.0012,1.10)'
# zoom OUT: z='if(eq(on,1),1.10,max(zoom-0.0012,1.0))'
ffmpeg -y -v error -loop 1 -i cena.png \
  -vf "scale=1350:2400,zoompan=z='min(zoom+0.0012,1.10)':d=140:s=1080x1920:fps=30,format=yuv420p" \
  -t 4.68 -r 30 clip0.mp4
```

`d = frames por cena` (140 frames @30fps = 4.68s). Alternar zoom-in/zoom-out entre cenas
dá ritmo. `format=yuv420p` já no clip evita erro no concat/xfade.

## 2. Encadear com xfade

`d` = duração por cena; com 6 cenas e 5 xfades de 0.5s: `6*d - 2.5 = duração do áudio` → `d = (audio + 2.5)/6`.

```bash
inputs="-i clip0.mp4 -i clip1.mp4 ... -i clip5.mp4 -i mix.wav"   # áudio é o ÚLTIMO input
# filter_complex:
[0:v][1:v]xfade=transition=fade:duration=0.5:offset=4.18[v1]
[v1][2:v]xfade=transition=fade:duration=0.5:offset=8.36[v2]
... (offset i = i*(d-0.5))
[v5]format=yuv420p[vout]
```

## 3. Áudio e export

🔴 **Pitfall clássico**: `-map "1:a"` falha com *"Stream map '1:a' matches no streams"*
quando o áudio NÃO é o input 1. Com N clips + áudio, o áudio é o input **N** (0-based) —
com 6 clips, `-map "6:a"`.

```bash
ffmpeg -y -v error <inputs> -filter_complex <fc> \
  -map "[vout]" -map "6:a" \
  -c:v libx264 -preset medium -crf 20 -r 30 \
  -c:a aac -b:a 192k -af "afade=t=out:st=24.6:d=0.8,aresample=48000" \
  -t 25.2 -movflags +faststart saidas/gojo_15s.mp4
```

- `afade out` no áudio (duração -0.6s) evita corte seco.
- `+faststart` = streaming-friendly (WhatsApp).
- Verificar depois: `ffprobe` (duração/tamanho) + `ffmpeg -af volumedetect -f null -`
  (mean ≈ -16 dB, max ≈ 0 dB = saudável).

## 4. Retomada pós-limite (fluxo validado)

O Claude estourou o limite 5h no passo do export — mas tinha salvo TUDO no projeto
(letra, `voz/beat.wav`, `voz/mix.wav` com ducking, 6 cenas, `gerar_beat.py`, `gerar_cenas.py`).
O Hermes retomou: inspecionou `projetos/<slug>/`, montou os clips + xfade + áudio com a
receita acima e entregou. **Regra**: todo pipeline de vídeo deve salvar artefatos
intermediários no projeto (nunca só em memória) — o fim pode ser retomado por qualquer agente.

## Notas

- Cenas procedurais (PIL+numpy, paleta medida da referência via keyframes) funcionaram bem
  sem credencial de imagem — arte própria + gradientes + texto estilizado + grão/vinheta.
- edge-tts: linhas de voz geradas como `voz/l01.mp3..l08.mp3`, mixadas com a batida
  (`gerar_beat.py`, numpy) com ducking da voz sobre o beat — impacto no refrão em ~12.5s.

## 5. Upgrade v2: rap masculino, cortes no beat e painéis

Validado em `gojo_15s_v2.mp4`: 27,30 s, 1080×1920, 30 fps, H.264 High/yuv420p,
AAC 48 kHz, −14,43 LUFS medidos, pico −1,05 dBTP e 24 mudanças visuais detectadas.

### 5.1 Voz rap edge-tts

Gerar **uma linha por arquivo**; não sintetizar o parágrafo inteiro:

```bash
edge-tts --voice pt-BR-AntonioNeural --rate='+15%' --pitch='+0Hz' \
  --text 'Seis Olhos abertos, eu enxergo o que ninguém vê.' \
  --write-media l01_raw.mp3

scripts/processar-voz-rap.sh l01_raw.mp3 l01_rap.wav -2.2
```

O script executa, nesta ordem: resample 48 kHz → pitch −2,2 st preservando duração →
HPF/LPF → reforço 190/320 Hz → presença 2,6 kHz → de-ess por corte em 6,8 kHz →
compressor 4,2:1 → limiter → double 22/37 ms filtrado e aberto no estéreo.

Encaixar cada arquivo num slot antes da mix. Se `d_raw > d_slot`, aplicar
`atempo=d_raw/d_slot`; nunca cortar o fim da palavra. Os inícios ficam no tempo forte,
mas os intervalos podem variar conforme o comprimento da linha.

### 5.2 Sidechain e loudnorm em dois passes

Áudio principal primeiro; sidechain vocal em segundo input:

```bash
ffmpeg -y -i beat.wav -i vocals.wav -filter_complex \
  "[1:a]apad=pad_dur=1,atrim=0:27.30,asplit=3[sc][dry][send]; \
   [0:a]volume=0.72[beat]; \
   [beat][sc]sidechaincompress=threshold=0.028:ratio=8:attack=4:release=170:makeup=1[duck]; \
   [dry]volume=1.10[voc]; \
   [send]highpass=f=180,lowpass=f=6800,aecho=0.82:0.70:92|184:0.12|0.055,volume=0.38[verb]; \
   [duck][voc][verb]amix=inputs=3:normalize=0,alimiter=limit=0.96[mix]" \
  -map '[mix]' -t 27.30 -ar 48000 -c:a pcm_s24le mix_pre.wav

ffmpeg -i mix_pre.wav -af 'loudnorm=I=-14:TP=-1:LRA=7:print_format=json' -f null -
# Repetir com measured_I/TP/LRA/thresh e target_offset devolvidos pelo passe 1.
```

### 5.3 Painel vertical e animação

Para material 16:9, criar antes um canvas 1080×1920: recorte no personagem, vinheta,
gradiente escuro inferior para apagar legenda antiga, halftone e speed lines. Depois:

```bash
scripts/animar-painel.sh painel.png clip_in.mp4 45 in
scripts/animar-painel.sh impacto.png clip_impacto.mp4 45 impact
```

Alternar `in`/`out`; reservar `impact` para drops, golpes e palavras fortes. O modo impacto
faz tremor dentro de uma sobra de 40 px, portanto não cria borda preta.

### 5.4 Cortes exatamente no beat

Calcular, não chutar:

```
passo = beats_por_plano × 60 / BPM
xfade = frames_do_clip / FPS − passo
offset_i = i × passo
```

Exemplo Gojo: 88 BPM, 2 beats/plano, 45 frames/30 fps → passo `1,363636 s`, xfade
`0,136364 s`. Com 20 clips:

```bash
[0:v][1:v]xfade=transition=fade:duration=0.136364:offset=1.363636[x1];
[x1][2:v]xfade=transition=wipeleft:duration=0.136364:offset=2.727273[x2]
```

Usar corte/fade curto como regra e `wipeleft`, `smoothup`, `circleopen` apenas nos marcos.
O modelo RM RAPS medido no primeiro trecho fez cerca de 20 mudanças em 30 s; a v2 ficou
na mesma ordem de grandeza, contra planos de ~4 s da v1.

### 5.5 Legenda e validação obrigatória

- Gerar ASS a partir dos **timings reais da voz processada**.
- Quebrar manualmente cada frase longa em duas linhas; não confiar no wrap automático.
- 9:16: fonte 50 px, margens L/R 90 e `MarginV=455`; validar frame em resolução cheia.
- Rodar `ffmpeg -v error -i final.mp4 -f null -` (decode completo), `ffprobe`, loudnorm,
  `volumedetect` e contato de 12–15 frames. “Renderizou” não significa “legenda cabe”.
