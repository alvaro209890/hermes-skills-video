# Sincronia musical e mapa temporal

Leia esta referência quando for encurtar a música, resincronizar legendas ou melhorar cortes no beat.

## Contrato de abertura

- A vinheta ocupa 0–4 s, mutada, enquanto a música toca desde 0 s.
- Fala narrativa e primeira estrofe cantada são eventos diferentes. Preserve uma fala curta e o
  título se eles adicionarem contexto; não force a letra a começar aos 4 s.
- Preferência editorial atual: primeira estrofe cantada em até aproximadamente 20 s depois da
  vinheta. Confirme com o pedido atual quando houver outra intenção.

## Emenda beat-locked

1. Meça BPM e ataques graves em vez de cortar por silêncio visual na waveform.
2. Proteja o fim da última fala e o ataque da próxima voz.
3. Prefira remover um número inteiro de beats ou compassos. Refine os dois pontos pelo mesmo delta
   para preservar a duração removida e a fase musical.
4. Minimize salto de amostra, inclinação e forma local. Use microcrossfade apenas quando o zero
   crossing não bastar; ele não pode borrar o kick.
5. Grave `cut_out`, `cut_in`, segundos/beats removidos, erro de grid e posição da primeira estrofe
   antes/depois em JSON.

## Um mapa para todos os consumidores

Para uma remoção `[cut_out, cut_in)` de duração `D`:

- `t <= cut_out`: mantenha `t`;
- `t >= cut_in`: use `t - D`;
- evento totalmente dentro da remoção: descarte;
- evento que cruza a emenda: apare de forma explícita e revise manualmente.

Aplique essa função ao áudio, `.ass`, plano visual e timestamps de referência. Não acumule offsets
manuais independentes e não some a duração da vinheta aos timestamps da música.

## Cortes visuais versus voz

- A legenda segue a voz medida pelo Whisper/letra oficial.
- O endpoint do plano visual pode fazer snap para o ataque mais próximo dentro de ±110 ms, desde
  que o novo plano não crie corte menor que 350 ms nem saia da janela limpa da fonte.
- Preserve a continuidade do conteúdo da fonte ao mover um boundary: desloque a entrada na fonte
  pelo mesmo delta do início visual.
- Em uma emenda, elimine microfragmentos acidentais. Prolongue o plano anterior e antecipe o plano
  seguinte quando isso criar um corte narrativo claro no ataque.

## Verificação

- emenda: erro de grid baixo, salto de amostra sem clique e waveform contínua;
- legendas: contagem antes/depois, eventos descartados justificados e amostras visuais no começo,
  meio e fim;
- plano: nenhuma lacuna, duração final igual ao áudio, todas as janelas limpas respeitadas;
- musicalidade: compare distância média e percentil 90 dos boundaries ao onset antes/depois;
- artefato: decodificação completa de master/compacto, 1080p30, AAC, faststart, loudness/true peak e
  auditoria do intermediário sem `.ass` em intervalos de 0,5 s.
