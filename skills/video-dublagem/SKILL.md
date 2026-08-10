---
name: video-dublagem
description: "Dubla vídeo para outro idioma preservando trilha e sincronia, com TTS gratuito, encaixe Rubber Band limitado a ±10% e QA de desvio alvo ≤150 ms. Use em pedidos como dubla para inglês/espanhol/português, põe em português ou quero este reel em vários idiomas."
---

# video-dublagem

> **📖 Arquitetura original: `~/Documentos/Planejamento_Skills_Video/PLANO_HERMES.md` (§3.1–§3.6, §2 protocolo, §5 gotchas).**
> Os estados/checklists antigos do plano são históricos; o estado executável abaixo prevalece.

## Estado: ENCAIXE LOCAL IMPLEMENTADO; SEPARAÇÃO AINDA DEPENDE DE DEMUCS (2026-08-10)

O encaixe e o QA por segmento funcionam. Neste PC, a dublagem integral ainda deve ser
bloqueada pelo doctor quando Demucs estiver ausente.

| Peça | Estado |
|---|---|
| `scripts/doctor.sh` | ✅ valida especificamente o perfil dublagem |
| `scripts/encaixar-fala.sh` | ✅ Rubber Band/formante, ±10%, slot exato e `.qa.json` |
| Demucs, transcrição, tradução e remix integral | ⚙️ pendente conforme dependências |

O doctor reconhece corretamente o **filtro** Rubber Band do FFmpeg; não exige o binário
homônimo. Demucs continua obrigatório para preservar trilha de um vídeo já mixado.

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

scripts/encaixar-fala.sh entrada.wav saida.wav slot_segundos [semitons=0]
#   Sai 3 se o tempo necessário passar de ±10%; gera saida.qa.json.
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
