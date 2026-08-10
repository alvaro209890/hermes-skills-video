---
name: video-dublagem
description: "Dubla um vídeo para outro idioma preservando a trilha original e a sincronia (desvio alvo ≤150 ms), entregando no WhatsApp."
tags: [video, dublagem, traducao, tts, demucs, sincronia, legendas]
platforms: [linux]
triggers:
  - dubla isso pra ingles
  - dubla pra espanhol
  - poe em portugues
  - quero esse reel em 3 idiomas
  - vídeo em idioma estrangeiro chegando no chat (oferecer dublagem)
---

# video-dublagem

> **📖 Referência completa: `~/Documentos/Planejamento_Skills_Video/PLANO_HERMES.md` (§3.1–§3.6, §2 protocolo, §5 gotchas).**
> Este SKILL.md é o mapa. O plano é a fonte de verdade.

## 🚧 Estado: BASE (2026-08-09)

Só a **base** está implementada. Nenhuma etapa de dublagem existe ainda.

| Peça | Estado |
|---|---|
| `scripts/doctor.sh` | ✅ funciona (wrapper do doctor canônico da `video-analise`) |
| Demucs, tradução com restrição, TTS, encaixe, remix, QA | ⛔ **não implementado** — fase seguinte |

⚠️ O doctor já reporta que **`Demucs` e `rubberband` não estão instalados** — as duas peças
centrais desta skill. Diga isso **antes** de aceitar um pedido de dublagem.

## O que a skill faz (quando pronta)

Troca o idioma da narração preservando a trilha original e a sincronia — inclusive em vídeos
de terceiros que o Álvaro quer em português.

## Quando usar

- "dubla isso pra inglês/espanhol", "põe em português" + link ou arquivo
- "quero esse reel em 3 idiomas"
- Vídeo em idioma estrangeiro chegando no chat → **oferecer** dublagem (não fazer sem pedir)

## Fluxo resumido

Detalhe passo a passo em **PLANO_HERMES.md §3.3**. Resumo:

```
0.  doctor                → scripts/doctor.sh                              ✅ implementado
1.  ⏸️ confirmar idioma/voz ANTES de gastar — é o pipeline mais caro
2.  separar               → Demucs htdemucs → vocals.wav + music.wav       ⛔ (não instalado)
3.  transcrever           → faster-whisper/WhisperX, timestamp por palavra ⛔
4.  segmentar             → por unidade de fala (pausa >200 ms), não por frase gramatical ⛔
5.  traduzir com restrição→ deepseek-v4-pro, orçamento de caracteres, 3 variantes/segmento ⛔
6.  TTS por segmento      → tool `tts` edge, voz equivalente no idioma alvo ⛔
7.  encaixe em cascata    → (a) variante que cabe → (b) absorver silêncio →
                            (c) rubberband ±10 % → (d) traduzir mais curto →
                            (e) marcar para revisão                        ⛔
8.  remix                 → narração + music.wav com ducking → loudnorm     ⛔
9.  legendas              → do áudio dublado REAL, não da tradução          ⛔
10. QA numérico           → desvio médio/p95/pior caso, meta ≤150 ms, relatado no chat ⛔
11. ⏸️ trocadilho intraduzível vira PERGUNTA, não invenção silenciosa
12. entrega incremental   → manda o inglês assim que sai, sem esperar o espanhol
```

**Por que o encaixe é o coração:** português é ~15–30 % mais longo que inglês. A sincronia se
resolve nas três camadas na ordem acima — tradução curta primeiro, time-stretch só depois.

## Scripts desta skill

```bash
scripts/doctor.sh [--curto|--json]
#   Wrapper — chama o doctor canônico em ../video-analise/scripts/doctor.sh
```

Para obter o material, use `../video-analise/scripts/baixar-video.sh`.

## Restrições

- **Custo zero, decisão do Álvaro (§7.6):** só `edge` TTS (tem vozes multi-idioma) e opções
  locais tipo Piper. **Sem ElevenLabs**, mesmo tendo API de dubbing.
- **Licenças:** XTTS-v2 é CPML (**proíbe uso comercial**); voz clonada de pessoa real exige
  autorização. Gravar motor e licença na saída.
- **Demucs em CPU compartilhada é lento** (~5–10× tempo real). Clipe de 4 min derruba a
  responsividade do Hermes → **avisar o tempo estimado antes** e agendar fora do horário de uso.
- **Job pesado roda local no acer** (§7.3); priorizar o PC Windows da IMAP por SSH quando estiver
  ligado — 🔧 previsto, não configurado.
- **Sem lip-sync.** Irrelevante para narração em off e anime edit; **bloqueante para talking head
  em close** — a skill precisa avisar, não entregar calada.
- **O Hermes não ouve o resultado.** O QA é numérico; a aprovação final é humana, no chat.
- **Prosódia:** TTS não reproduz ironia — e o tom das referências *é* irônico.

## Protocolo de conversa

Compartilhado pelas três skills: **`../video-analise/references/protocolo-whatsapp.md`**.
