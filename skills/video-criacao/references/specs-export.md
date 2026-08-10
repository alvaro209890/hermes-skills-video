# Specs de export

> Fonte: `README.md` §6 ("Especificações de export") · `PLANO_HERMES.md` §2.3 passos 9–10.
> Estes números vão fixados no `videospec.json` — não são sugestão.

## 9:16 (Reels / Shorts / TikTok) — principal

| | |
|---|---|
| Resolução | 1080 × 1920 |
| FPS | 30 |
| Vídeo | H.264 High, CRF 18–20 (ou ~12 Mbps), `yuv420p` |
| Áudio | AAC 192 kbps, 48 kHz |
| Container | MP4 com `-movflags +faststart` |

## 16:9 (YouTube)

1920 × 1080, mesmos codecs, CRF 18. **Reenquadrar**, nunca *letterbox*.

## Safe area 9:16 (regra prática)

Texto crítico entre **x 100–860** e **y 300–1450**.
A autoverificação com `vision` (§2.3 passo 11) checa exatamente isto: legenda cortada?
dentro da safe area? texto legível sobre o fundo?

## Áudio

- Narração/conteúdo geral: −14 LUFS-I.
- Música curta/rap: −13 a −11 LUFS-I, LRA 1,5–4 LU.
- Em ambos: **AAC final decodificado ≤−1 dBTP**. `loudnorm` em dois passes e nova
  medição depois do encode; o AAC nativo pode criar picos interamostra que não existem no WAV.

## Encode nesta máquina

VAAPI está disponível (`h264_vaapi`, `hevc_vaapi`, `av1_vaapi` — GPU AMD Lucienne) e é
**muito mais rápido que CPU**. Confirmado pelo `doctor.sh`.

```
-vaapi_device /dev/dri/renderD128 -vf 'format=nv12,hwupload' -c:v h264_vaapi
```

⚠️ A iGPU serve para **encode**, não para gerar imagem/vídeo local (11 GB de RAM, sem GPU
dedicada → difusão local está fora).
