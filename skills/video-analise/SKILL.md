---
name: video-analise
description: "Analisa um vídeo (Reel, Short, TikTok, YouTube) — baixa, transcreve, extrai frames, enxerga o estilo — e devolve ANALISE.md com [mm:ss] no WhatsApp."
tags: [video, analise, reels, shorts, tiktok, youtube, transcricao, keyframes, estilo]
platforms: [linux]
triggers:
  - analisa esse video
  - analisa esse reel
  - olha esse reel
  - que estilo é esse
  - por que esse video foi bem
  - extrai o roteiro desse video
  - qualquer URL de youtube.com, youtu.be, instagram.com/reel, tiktok.com
  - vídeo enviado como arquivo no chat
---

# video-analise

> **📖 Referência completa: `~/Documentos/Planejamento_Skills_Video/PLANO_HERMES.md` (§0, §1.1–§1.6, §2, §5).**
> Este SKILL.md é o mapa. O plano é a fonte de verdade — leia antes de executar o pipeline.

## 🚧 Estado: BASE (2026-08-09)

Só a **base** está implementada. O pipeline completo é a fase seguinte.

| Peça | Estado |
|---|---|
| `scripts/doctor.sh` | ✅ funciona — diagnóstico do ambiente |
| `scripts/baixar-video.sh` | ✅ funciona — download com os gotchas conhecidos |
| transcrição, cortes, keyframes, `vision`, `ANALISE.md` | ⛔ **não implementado** — fase seguinte |

**Não prometa análise completa ao Álvaro enquanto isto estiver aqui.** O que dá para
fazer hoje: rodar o doctor e baixar o material.

## O que a skill faz (quando pronta)

Recebe um link (ou um vídeo mandado no chat) e devolve, sozinho e de forma assíncrona,
um `ANALISE.md` com o eixo visual lido pela própria tool `vision` — mais um resumo curto
no chat.

## Quando usar

- Qualquer URL de `youtu.be`, `youtube.com/shorts`, `instagram.com/reel`, `tiktok.com`
- Vídeo enviado como **arquivo** no chat (já está em `~/.hermes/cache/videos/` — pula o download)
- "analisa esse aqui", "que estilo é esse", "por que esse vídeo foi bem", "extrai o roteiro"
- Link + "quero fazer igual" → encadeia direto na `video-criacao`

**Regra de disparo:** link solto **não** dispara o pipeline (custa minutos, disco e API).
Responder curto e perguntar — salvo quando a mensagem já traz a intenção.

## Fluxo resumido

Detalhe passo a passo em **PLANO_HERMES.md §1.3**. Resumo:

```
0. doctor          → scripts/doctor.sh          ✅ implementado
1. ⏸️ confirmar     → clarify ("Analiso? ~4 min")
2. aceite em segundos + enfileirar no kanban
3. obter vídeo     → scripts/baixar-video.sh    ✅ implementado
                     (Instagram com login → tool `browser`; nunca "não consegui")
4. áudio + faixas  → ffmpeg / Demucs            ⛔ fase seguinte
5. transcrição     → faster-whisper (medium)    ⛔ fase seguinte
6. cortes e ritmo  → PySceneDetect / librosa    ⛔ fase seguinte
7. keyframes       → ffmpeg (~15)               ⛔ fase seguinte
8. 👁️ ver os frames → tool `vision` (Groq llama-4-scout), lotes + cache   ⛔ fase seguinte
9. mixagem         → loudnorm (LUFS, ducking)   ⛔ fase seguinte
10. ANALISE.md + resumo ≤8 linhas + 2–3 keyframes por MEDIA:   ⛔ fase seguinte
```

## Scripts desta skill

```bash
scripts/doctor.sh [--curto|--json]
#   Verifica ffmpeg (+ filtros + VAAPI), yt-dlp, faster-whisper, edge-tts, tesseract,
#   Demucs, PySceneDetect, librosa, rubberband, disco, e a PRESENÇA (não o valor) das
#   chaves em ~/.hermes/.env. NÃO INSTALA NADA. Sai 1 se faltar algo da base.

scripts/baixar-video.sh <URL> [--slug s] [--cookies chrome] [--audio-so] [--dry-run]
#   Baixa para ~/Documentos/Video_Studio/entradas/<slug>/{fonte.*, fonte.info.json}
```

## Restrições

- **Custo zero.** Sem API paga. TTS é `edge`; visão é a Groq já configurada (decisões §7.2/§7.6).
- **Nada de instalar por conta própria** nesta fase. O doctor **reporta**, o Álvaro decide.
- **Um job pesado por vez** — Whisper e Demucs competem com gateway, WhatsApp e Postgres.
- **Toda afirmação de estilo precisa de `[mm:ss]` ou número.** "Edição dinâmica" é proibido;
  "34 cortes/min, mediana 1,8 s por plano" é o padrão.
- **Não usar a legenda do YouTube** (`timedtext` devolve 0 byte). Transcrição própria, sempre.
- Se a visão falhar, **dizer que a análise saiu incompleta** — nunca fingir que viu.
- Não usar o perfil de trabalho do navegador para downloads pessoais.

## Gotchas que mais custam (detalhe em PLANO_HERMES §5)

1. **`yt-dlp` do apt (2024.04.09) está quebrado para YouTube** — `baixar-video.sh` recusa o
   download e manda instalar via `uv tool install yt-dlp`.
2. **Heredoc dispara aprovação** (`approvals.mode: manual`, janela de 60 s) — inviável pelo
   celular. Por isso os scripts são **arquivos** em `scripts/`, executados como arquivo.
3. **`vision_analyze` devolve texto, não pixels** — pergunta nova sobre o mesmo frame = chamada
   nova. Pedir tudo num prompt só.
4. **Job longo tem que ser processo em background** (`gateway_timeout` 3600 s) que avisa o
   progresso por `hermes send --to whatsapp`.
5. **Normalizar a URL** — Instagram cola `?igsh=…`, YouTube cola `&list=` (que baixaria a
   playlist inteira). O script já limpa.

## Protocolo de conversa

Compartilhado pelas três skills: **`references/protocolo-whatsapp.md`**.
