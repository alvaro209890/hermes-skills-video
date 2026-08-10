# Presets de identidade

> Fonte: `PLANO_HERMES.md` §2.6 (passo 1: "definir presets para não perguntar nada além do tema")
> e §7 (decisões do Álvaro em 2026-08-09).
>
> 🚧 **Base.** Os presets abaixo são o ponto de partida declarado no plano. Os valores exatos de
> fonte e cor só serão fechados depois da primeira análise real de um Reel do @silv.mind
> (medidos pela tool `vision`, não chutados).

## Por que preset existe

**Orçamento de 3 perguntas por vídeo.** Tudo que puder virar default declarado, vira:

> "vou de 9:16, 30 s, voz Francisca, estilo jjk-dark — só falar se quiser diferente."

## `jjk-dark` (padrão — nicho anime edit brasileiro, JJK)

| Campo | Valor |
|---|---|
| `formato.principal` | `9:16` (também `16:9`), 30 fps |
| `duracao_alvo_s` | 30 |
| `narracao.motor` | `edge-tts` (grátis — decisão §7.6, **sem ElevenLabs**) |
| `narracao.voz` | `pt-BR-FranciscaNeural` |
| `narracao.ritmo` | `+8%` |
| `legendas.estilo` | `karaoke-palavra`, `safe_area: true` |
| `audio.lufs_alvo` | −14 · `ducking_db` −8 |
| `cor_destaque` | `#7B2FF7` (a confirmar por `vision`) |
| fonte | ⚠️ **a medir** — não inventar |

## Vozes edge disponíveis (pt-BR)

`pt-BR-FranciscaNeural` (padrão) · `pt-BR-AntonioNeural` (masc.) ·
`pt-BR-ThalitaMultilingualNeural` (multi-idioma — útil na dublagem).

**Só grátis.** Se precisar de mais timbre, alternativa é local (Piper), nunca API paga.

## Origem das cenas, por ordem de custo (decisão §7.1/§7.2)

1. **material próprio / licenciado** — hoje o caminho principal;
2. **busca de imagens** + edição de estilo;
3. **`image_gen` + `zoompan`** (Ken Burns) — resolve ~80 % do Modo A, custo zero
   — ⚠️ hoje **sem credencial** no `.env`;
4. **Grok (imagem) via API do Cursor** — upgrade opcional, 🔧 **previsto, não configurado**;
5. clipe de anime como **último recurso** (direito autoral — README §9.1).
