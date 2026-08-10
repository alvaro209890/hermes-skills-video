# Exemplo Gojo v3

Scripts do caso real usado para validar a cadeia de rap e edição das skills. O resultado medido
foi um MP4 1080×1920/30 fps de 30 s, H.264 High/AAC 48 kHz, −12,8 LUFS-I, LRA 1,7 e
true peak AAC decodificado de −1,1 dBFS.

## O que está incluído

- beat procedural original a 95 BPM;
- oito tomadas Edge Andrew Multilingual, Rubber Band/formante, EQ, de-ess e doubles;
- sidechain, ambience, loudnorm e proteção de pico pós-AAC;
- criação de 24 painéis em três linguagens e render com grade de 1,263158 s;
- ASS karaokê, letra/timings e validação no `build_v3.sh`.

## O que não está incluído

Vídeos, áudios e quadros protegidos usados como referência; imagens-base do anime; vozes
renderizadas; painéis; arquivos intermediários; MP4 final. Eles não devem ser versionados.

`preparar_paineis_v3.py` espera 12 imagens verticais autorizadas em
`assets_v2/paineis/painel_01.png` … `painel_12.png`. Depois:

```bash
chmod +x build_v3.sh
./build_v3.sh
```

Dependências leves: Python 3, NumPy, Pillow, FFmpeg com filtro `rubberband`, ffprobe e edge-tts.
Leia `skills/video-criacao/references/rap-v3-modelos.md` antes de adaptar voz ou grade.
