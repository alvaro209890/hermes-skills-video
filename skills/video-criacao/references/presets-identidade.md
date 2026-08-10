# Presets de identidade

> Fonte: `PLANO_HERMES.md` §2.6 (passo 1: "definir presets para não perguntar nada além do tema")
> e §7 (decisões do Álvaro em 2026-08-09).
>
> 🚧 **Base.** Os presets abaixo são o ponto de partida declarado no plano. Os valores exatos de
> fonte e cor só serão fechados depois da primeira análise real de um Reel do @silv.mind
> (medidos pela tool `vision`, não chutados).

## Por que preset existe

**Orçamento de 3 perguntas por vídeo.** Tudo que puder virar default declarado, vira:

> "vou de 9:16, 30 s, voz Andrew processada para rap, estilo jjk-dark — só falar se quiser diferente."

## `jjk-dark` (padrão — nicho anime edit brasileiro, JJK)

| Campo | Valor |
|---|---|
| `formato.principal` | `9:16` (também `16:9`), 30 fps |
| `duracao_alvo_s` | 30 |
| `narracao.motor` | `edge-tts` (grátis — decisão §7.6, **sem ElevenLabs**) |
| `narracao.voz` | `en-US-AndrewMultilingualNeural` em rap; `FranciscaNeural` em narração comum |
| `narracao.ritmo` | uma tomada por linha; edge `+12%` a `+18%`; encaixe posterior no beat |
| `legendas.estilo` | `karaoke-palavra`, `safe_area: true` |
| `audio.lufs_alvo` | −12,5 para música curta · `ducking_db` −2 a −4 |
| `cor_destaque` | `#7B2FF7` (a confirmar por `vision`) |
| fonte | ⚠️ **a medir** — não inventar |

## Vozes edge disponíveis (pt-BR)

`pt-BR-FranciscaNeural` (padrão) · `pt-BR-AntonioNeural` (masc.) ·
`pt-BR-ThalitaMultilingualNeural` (multi-idioma — útil na dublagem).

**Só grátis.** Se precisar de mais timbre, alternativa é local (Piper), nunca API paga.

### Preset vocal `rap-br-masc-v3` (validado no Gojo)

- Andrew Multilingual, rate `+15%`; Rubber Band −1,5 st com `formant=preserved`.
- EQ: HPF 68 Hz; +2,6 dB/170 Hz; +1,2 dB/300 Hz; −1,2 dB/520 Hz;
  +1,8 dB/2,55 kHz; −1,8 dB/7,1 kHz; de-esser moderado.
- Compressor 3,6:1, ataque 7 ms, release 95 ms; softclip 4x.
- Double da mesma tomada: 18 ms à esquerda/−18 dB e 31 ms à direita/−19,5 dB, filtrado.
- Não concatenar um parágrafo. Sintetizar uma linha curta por arquivo e encaixar cada início no tempo forte.
- Nunca remover silêncios internos com `stop_periods=-1`; aparar só as bordas com `areverse`.
- Rejeitar tomada que exija `tempo>1.15`.

## Origem das cenas, por ordem de custo (decisão §7.1/§7.2)

1. **material próprio / licenciado** — hoje o caminho principal;
2. **busca de imagens** + edição de estilo;
3. **`image_gen` + `zoompan`** (Ken Burns) — resolve ~80 % do Modo A, custo zero
   — ⚠️ hoje **sem credencial** no `.env`;
4. **Grok (imagem) via API do Cursor** — upgrade opcional, 🔧 **previsto, não configurado**;
5. clipe de anime como **último recurso** (direito autoral — README §9.1).
