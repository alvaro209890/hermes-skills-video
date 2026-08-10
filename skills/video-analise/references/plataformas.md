# Plataformas — o que cada uma exige (e o que já quebrou)

> Fonte: `README.md` §3.4 e §6 · `PLANO_HERMES.md` §1.3, §5.
> Verificado em 2026-08-09. **Plataformas mudam sem aviso** — quando algo aqui falhar,
> o `doctor.sh` deve ser o primeiro a detectar, e este arquivo o primeiro a ser corrigido.

## YouTube

- ❌ **`yt-dlp` do apt (2024.04.09) está quebrado**: `Requested format is not available`
  (extractor desatualizado). `scripts/baixar-video.sh` **recusa** o download e manda instalar:
  `uv tool install yt-dlp`. Nunca confiar no pacote do apt.
- ❌ **Transcrição pelo `timedtext` não funciona**: devolve corpo vazio (0 byte) mesmo listando
  a trilha `pt/asr` — o YouTube passou a exigir *proof-of-origin token*.
  **Decisão de arquitetura: transcrição própria com `faster-whisper`, sempre.**
- Links colam `&list=` e `?si=` — `--no-playlist` e a normalização de URL do script tratam isso
  (um `&list=` sem `--no-playlist` baixaria a playlist inteira).

## Instagram (Reels)

- ❌ Sem login: `Requested content is not available, rate-limit reached or login required`.
- Caminhos, nesta ordem:
  1. `baixar-video.sh <url> --cookies chrome` (`--cookies-from-browser`);
  2. se falhar, **o próprio Hermes abre a tool `browser`** na sessão logada, carrega o Reel e
     captura o arquivo (PLANO_HERMES §1.3 passo 4). **Nunca responder "não consegui".**
- Links vêm com `?igsh=…` — o script normaliza.
- ⚠️ Não usar o perfil de trabalho do navegador para isso.

## TikTok

- Geralmente baixa sem login. Vídeos até 10 min.

## Limites de duração por plataforma

| Plataforma | Máximo | Ideal |
|---|---|---|
| Reels | 3 min | 15–45 s |
| Shorts | 3 min | 15–45 s |
| TikTok | 10 min | 15–60 s |

## Quando o vídeo já veio pelo chat

Se o Álvaro **mandou o arquivo**, o bridge já salvou em `~/.hermes/cache/videos/` e o caminho
absoluto chega ao agente: **pular o download inteiro**. Não rebaixar o que já está no disco.
