---
name: video-criacao
description: "Cria vídeo do briefing ao MP4 — roteiro, cenas/painéis animados, voz edge-tts processada (inclusive rap masculino), beat, legendas, render 9:16/16:9 e entrega no WhatsApp. Use em pedidos como: faz um reel/short, monta no estilo de uma referência, transforma áudio ou texto em vídeo, ou faz um igual após uma análise."
---

# video-criacao

> **📖 Arquitetura original: `~/Documentos/Planejamento_Skills_Video/PLANO_HERMES.md` (§2 protocolo, §2.1–§2.6, §5 gotchas, §7 decisões).**
> Os estados/checklists antigos do plano são históricos; o estado executável abaixo prevalece.

## Estado: PIPELINE LOCAL V3 VALIDADO (2026-08-10)

O pipeline local gratuito foi executado ponta a ponta em três versões do clipe Gojo. A v3
foi recalibrada contra Gojo, Mahoraga, Toji e Kashimo do RM RAPS: voz, grade, edição e master.
Entrega automática pelo WhatsApp ainda depende do protocolo do canal.

| Peça | Estado |
|---|---|
| `scripts/doctor.sh` | ✅ wrapper do doctor canônico da `video-analise` |
| voz rap Edge + Rubber Band/formante/EQ/compressão/double | ✅ `scripts/processar-voz-rap.sh` |
| painel vertical + zoom/tremor | ✅ `scripts/animar-painel.sh` |
| grade de cortes/microimpactos | ✅ `scripts/calcular-grade.py` |
| validação de MP4/decode/loudness/faststart | ✅ `scripts/validar-export.sh` |
| beat procedural, sidechain, ASS karaokê, xfade, H.264/AAC | ✅ `references/montagem-ffmpeg.md` |
| entrega/retomada automática pelo WhatsApp | ⚙️ seguir protocolo compartilhado; não presumir concluída |

## O que a skill faz (quando pronta)

Produz o vídeo inteiro a partir de um pedido no chat — roteiro, cenas, narração, edição,
export 9:16 e 16:9 — e entrega o arquivo como anexo no WhatsApp. O Álvaro **nunca abre terminal**.

## Quando usar

- "faz um reel sobre `<tema>`", "cria um short de 30s explicando `<coisa>`"
- "monta um vídeo no estilo do `<slug analisado>`"
- "transforma esse áudio/texto em vídeo" (nota de voz ou documento no chat)
- Por `hermes cron`: pauta semanal recorrente

⚠️ **AMV do canal MUGEN RAPS não é esta skill.** Música do canal + anime = skill
`creative/amv-rap-geek`, com as ferramentas do `~/Documentos/Video_Studio` (`estudio.py` cria,
`publicar.py` publica). O padrão aprovado pelo Álvaro em 17/09/2026 é a **v4 do Naruto**: legenda
cinética palavra por palavra (`ferramentas/legenda_cinetica.py`), **sem** karaokê `\k`, e efeitos
por chave de plano. O `.ass` karaokê desta skill vale para reel/short genérico.

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
7.  narração              → Edge; rap masc. usa Andrew Multilingual + cadeia v3       ✅
8.  legendas              → timings da voz processada → .ass karaokê                  ✅
9.  edição                → cortes no beat + zoom/tremor + xfade + ass + ducking       ✅
10. encode                → libx264 CRF 18–20; VAAPI é alternativa                    ✅
11. 👁️ autoverificação     → ffprobe + decode + loudnorm + 4–6 keyframes               ✅
12. entrega               → MEDIA:/…/final_9x16.mp4 + legenda do post + hashtags      ⛔
13. ⏸️ feedback            → ["Tá bom","Refaz a narração","Muda o corte final"]        ⛔
```

## Scripts desta skill

```bash
scripts/doctor.sh [--curto|--json]
#   Wrapper — chama o doctor canônico em ../video-analise/scripts/doctor.sh
#   (um só diagnóstico para as três skills; não duplicar a lógica)

scripts/processar-voz-rap.sh entrada.mp3 saida.wav [-1.5] [tempo=1.0]
#   48 kHz; Rubber Band/formante, EQ, de-ess, compressão e double 18/31 ms.

scripts/animar-painel.sh imagem.png clip.mp4 [45] [in|out|impact]
#   Clip 1080×1920/30 fps com zoompan ou tremor de impacto.

scripts/calcular-grade.py 95 30 --beats-por-plano 2 --frames-por-clip 42
scripts/validar-export.sh final.mp4
```

Para baixar material de referência, use `../video-analise/scripts/baixar-video.sh`.

**Montagem/render (etapas 7-10) — receita completa e VALIDADA em 2026-08-10** no clipe
"GOJO — ACIMA DO INFINITO" v3 (30 s, 1080×1920): voz rap processada, 24 planos,
27 mudanças visuais detectadas, painel/zoom/tremor + microxfade + ASS karaokê + sidechain +
master protegido para AAC + export libx264/AAC `+faststart` — `references/montagem-ffmpeg.md`. Inclui o pitfall do
`-map` do áudio (índice = nº de vídeos) e o padrão de retomada pós-limite (artefatos sempre
salvos em `~/Documentos/Video_Studio/projetos/<slug>/`).

## Restrições

- **Custo zero, decisão do Álvaro (§7.6):** só `edge` TTS. **Sem ElevenLabs, sem API paga de voz.**
- Para rap masculino BR, começar por `en-US-AndrewMultilingualNeural` (`+15%`, pitch −1,5 st);
  ele venceu Antônio e Brian na calibração Gojo. Francisca continua adequada a narração comum.
  Nunca chamar TTS cru de "voz igual à referência": gerar preview, ouvir e só então mixar.
- TTS não vira performance humana/RVC apenas com EQ. O processamento melhora timbre e presença;
  o flow vem principalmente de uma linha por tomada, encaixe temporal e pausas assimétricas.
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
- **Áudio musical curto:** −13 a −11 LUFS-I, LRA 1,5–4 LU, AAC decodificado ≤−1 dBTP.
  Medir o MP4 final: um WAV em −1 dBTP pode ultrapassar 0 dBTP após AAC.

## Protocolo de conversa

Compartilhado pelas três skills: **`../video-analise/references/protocolo-whatsapp.md`**.
