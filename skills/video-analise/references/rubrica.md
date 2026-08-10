# Rubrica do `ANALISE.md`

> Fonte: `PLANO_HERMES.md` §1.3 passo 11 + `README.md` §3.
> **Regra de ouro: toda afirmação de estilo precisa de `[mm:ss]` ou de um número.**
> "Edição dinâmica" é proibido. "34 cortes/min, mediana de 1,8 s por plano" é o padrão.

## Seções obrigatórias

1. **Veredito** (3 linhas) — o que esse vídeo faz bem, e o que dá para replicar.
2. **Estrutura com `[mm:ss]`** — hook / desenvolvimento / virada / punchline / CTA.
3. **Roteiro transcrito** — texto com timestamps.
4. **Ritmo** — cortes/min, média e **mediana** de duração de plano, desvio.
   Modo B: BPM e **% de cortes na batida** (±80 ms).
5. **Estilo visual** — paleta dominante, enquadramento, tipo de material
   (clipe de anime / arte estática / gameplay / talking head).
6. **Transições** — corte seco, fade, zoom, whip — com contagem.
7. **Legendas** — fonte, peso, contorno, posição, karaokê sim/não, dentro da safe area?
8. **Áudio** — LUFS integrado, pico, faixa dinâmica, ducking medido;
   voz humana / TTS / processada por IA (com o grau de confiança).
9. **Fórmula extraída** — o esqueleto reutilizável, em blocos de tempo.
10. **Rascunho de `videospec.json`** — pronto para a `video-criacao` consumir.

## O que NÃO fazer

- Não afirmar nada visual sem ter passado o frame pela tool `vision`.
- Se a visão falhar, **dizer que a análise saiu incompleta** — nunca preencher de suposição.
- Não usar a legenda automática do YouTube (`timedtext` devolve 0 byte). Transcrição própria.
- Não confundir o STT do chat (modelo `base`, fraco) com a transcrição da análise
  (`medium` no dia a dia, `large-v3` no passe final).

## Métrica que o Álvaro pediu explicitamente

O teto de audiência **não vem do pipeline técnico**: RM RAPS tem 3,08 M e 14,7 k views com a
**mesma** fórmula. O que muda é o personagem/tema. A análise deve capturar isso como **métrica**
(views, data, tema, personagem), não só como estética.
