---
name: video-criacao
description: "Cria um vídeo inteiro do briefing ao MP4 — roteiro, cenas (image_gen+zoompan), narração edge TTS, legendas, render 9:16 e 16:9 — e entrega no WhatsApp."
tags: [video, criacao, reels, shorts, roteiro, tts, ffmpeg, zoompan, render]
platforms: [linux]
triggers:
  - faz um reel sobre
  - cria um short de 30s explicando
  - monta um video no estilo do
  - transforma esse audio em video
  - transforma esse texto em video
  - faz um igual (depois de uma análise)
---

# video-criacao

> **📖 Referência completa: `~/Documentos/Planejamento_Skills_Video/PLANO_HERMES.md` (§2 protocolo, §2.1–§2.6, §5 gotchas, §7 decisões).**
> Este SKILL.md é o mapa. O plano é a fonte de verdade.

## 🚧 Estado: BASE (2026-08-09)

Só a **base** está implementada. Nenhuma etapa de produção existe ainda.

| Peça | Estado |
|---|---|
| `scripts/doctor.sh` | ✅ funciona (wrapper do doctor canônico da `video-analise`) |
| roteiro, `videospec.json`, cenas, TTS, legendas, render | ⛔ **não implementado** — fase seguinte |

**Não aceite "faz um reel" como se fosse entregar um MP4 hoje.** Rodar o doctor é o que existe.

## O que a skill faz (quando pronta)

Produz o vídeo inteiro a partir de um pedido no chat — roteiro, cenas, narração, edição,
export 9:16 e 16:9 — e entrega o arquivo como anexo no WhatsApp. O Álvaro **nunca abre terminal**.

## Quando usar

- "faz um reel sobre `<tema>`", "cria um short de 30s explicando `<coisa>`"
- "monta um vídeo no estilo do `<slug analisado>`"
- "transforma esse áudio/texto em vídeo" (nota de voz ou documento no chat)
- Por `hermes cron`: pauta semanal recorrente

## Fluxo resumido

Detalhe passo a passo em **PLANO_HERMES.md §2.3**. Resumo:

```
0.  doctor                → scripts/doctor.sh            ✅ implementado
1.  ⏸️ briefing            → clarify, no MÁXIMO 2 perguntas (estilo e duração)
2.  roteiro               → fórmula do Modo A, ~2,7 palavras/s (30 s ≈ 80 palavras)  ⛔
3.  ⏸️ aprovação do texto  → clarify ["Renderiza","Encurta","Refaz o gancho"]         ⛔
4.  videospec.json        → preenchido do preset                                     ⛔
5.  cenas, por custo      → material próprio > image_gen + zoompan > (video_gen só cli) ⛔
6.  ⏸️ aviso de custo/tempo antes de qualquer chamada paga                            ⛔
7.  narração              → tool `tts` edge pt-BR-FranciscaNeural, 1 arquivo/cena     ⛔
8.  legendas              → da narração SINTETIZADA (não do roteiro) → .ass karaokê   ⛔
9.  edição                → ffmpeg concat + xfade + ass + ducking + loudnorm -14 LUFS ⛔
10. encode                → h264_vaapi (GPU AMD, disponível nesta máquina)            ⛔
11. 👁️ autoverificação     → 4–6 keyframes do render pela tool `vision`                ⛔
12. entrega               → MEDIA:/…/final_9x16.mp4 + legenda do post + hashtags      ⛔
13. ⏸️ feedback            → ["Tá bom","Refaz a narração","Muda o corte final"]        ⛔
```

## Scripts desta skill

```bash
scripts/doctor.sh [--curto|--json]
#   Wrapper — chama o doctor canônico em ../video-analise/scripts/doctor.sh
#   (um só diagnóstico para as três skills; não duplicar a lógica)
```

Para baixar material de referência, use `../video-analise/scripts/baixar-video.sh`.

## Restrições

- **Custo zero, decisão do Álvaro (§7.6):** só `edge` TTS. **Sem ElevenLabs, sem API paga de voz.**
- **`image_gen` + `zoompan` é o padrão (§7.2)** — Ken Burns resolve ~80 % do Modo A e custa zero.
  `video_gen` **não existe no toolset `whatsapp`** (só no `cli`).
- **Sem credencial de imagem generativa hoje** — o `.env` tem só `DEEPSEEK_API_KEY` e `GROQ_API_KEY`.
  Upgrade previsto: **Grok (imagem) via API do Cursor** (§7.1) — **previsto, não configurado**.
  Enquanto isso: material próprio + busca de imagens + `zoompan`.
- **Máximo 3 perguntas por vídeo.** O resto é default declarado: *"vou de 9:16, 30 s, voz Francisca,
  estilo jjk-dark — só falar se quiser diferente."*
- **Aprovação do texto antes do render** — texto é barato de revisar, render não é.
- **Job pesado roda local no acer** (§7.3). Quando o PC Windows da IMAP (pcque001imap, Tailscale)
  estiver ligado, ele é o de melhor processamento e a skill deve **priorizar executar lá** por SSH
  — 🔧 host/credenciais ainda a definir. Não é para configurar agora.
- **Direito autoral:** arte própria é o caminho preferencial, não o plano B (README §9.1).
- Um render por vez — compete com os serviços do Hermes.

## Specs de export (fixar no `videospec.json`)

- **9:16** 1080×1920, 30 fps, H.264 High, CRF 18–20, `yuv420p`, AAC 192 kbps 48 kHz, `+faststart`
- **16:9** 1920×1080, mesmos codecs, CRF 18 — **reenquadrar**, nunca *letterbox*
- **Safe area 9:16:** texto crítico entre x 100–860 e y 300–1450
- **Áudio:** −14 LUFS integrado, pico −1 dBTP

## Protocolo de conversa

Compartilhado pelas três skills: **`../video-analise/references/protocolo-whatsapp.md`**.
