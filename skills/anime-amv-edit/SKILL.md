---
name: anime-amv-edit
description: "Crie AMVs canônicos com beat e legendas sincronizados."
version: 2.0.0
author: Álvaro (alvaro209890), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [anime, amv, video-edit, rap-geek, ass, ffmpeg]
    related_skills: [amv-rap-geek]
---

# Anime AMV Edit

Crie AMVs completos de Rap Geek com narrativa canônica, fontes limpas, cortes musicais e legendas
cinematográficas. Use `amv-rap-geek` quando precisar do fluxo completo de publicação e das regras
específicas do canal.

## Quando usar

- criar ou revisar AMV de anime/Rap Geek;
- encurtar uma abertura instrumental sem quebrar o beat;
- resincronizar áudio, `.ass` e plano visual;
- melhorar cortes em relação a kicks, 808 e ataques musicais.

Não use para substituir material oficial por fan-animation, CGI ou cenas de outra obra.

## Regras invariantes

1. **Fonte pura:** audite cada fonte a 1 fps e registre janelas limpas. Nome, título e thumbnail não
   provam o conteúdo. Barre no validador qualquer plano fora dessas janelas.
2. **Sem contaminação:** remova marca d'água e legenda de dublagem antes da montagem. Audite o
   intermediário sem `.ass` a cada 0,5 s para não confundir texto de terceiro com a legenda musical.
3. **Vinheta 0–4 s (só vídeo longo):** use a intro oficial **v2** mutada,
   `~/Documentos/Video_Studio/assets/intro/intro_mugen_v2_169_mudo.mp4`; a música começa em 0 s.
   A v1 (`nova_intro_mugen_oficial.mp4`) está aposentada — o emblema dela era o logo do BTS.
   🚫 Mas **vídeo já publicado fica com a v1**: não reenviar nem trocar abertura do que já
   está no ar. A v2 vale da próxima faixa em diante.
   **Short, Reel, TikTok e corte vertical não levam vinheta**: entram direto no conteúdo.
   Não insira card estático de capa e não adicione `+4 s` ou `+7,5 s` aos timestamps da faixa.
4. **Abertura com intenção:** diferencie fala narrativa da primeira estrofe. A letra não precisa
   começar aos 4 s; como referência editorial, faça a estrofe entrar em até ~20 s depois da vinheta.
5. **Corte vertical 9:16 enquadra, nunca recorta:** frame 16:9 inteiro centralizado
   (`scale=1080:-2`) sobre fundo borrado do mesmo frame (`gblur=sigma=35`). Sem `crop`
   no primeiro plano — center-crop decepa rosto e corta a ponta da legenda. Vale para
   TikTok, Reels e Shorts do YouTube. Confira um frame antes de publicar.
6. **Narrativa 1:1:** cada cena deve responder ao personagem, evento ou habilidade citada na letra.

## Emenda e sincronia

1. Meça BPM e ataques; proteja a cauda da última fala e o ataque do próximo vocal.
2. Remova um número inteiro de beats/compassos e refine os dois pontos pelo mesmo delta em zero
   crossing. Um microcrossfade (ex: 8–10 ms) é aceitável para eliminar estalos sem borrar o ataque do kick/808.
3. Registre `cut_out`, `cut_in`, duração/beats removidos, erro de grid e primeira estrofe antes/depois.
4. Use um único mapa temporal por trechos para áudio, `.ass`, Whisper, plano visual e QA:
   tempos após `cut_in` recebem `-(cut_in-cut_out)`; eventos dentro da remoção são descartados.
5. A legenda segue a voz. O corte visual pode fazer snap ao onset mais próximo dentro de ±110 ms,
   sem criar plano menor que 350 ms nem sair da janela limpa.
6. **Autocorrelação com envelope downsampled:** para detecção rápida e robusta de BPM em faixas longas (>3 min), calcule o envelope RMS/médio em 1 kHz (downsample) antes da autocorrelação, evitando timeouts de CPU em full-rate 44.1 kHz.

A etapa termina quando todos os consumidores usam o mesmo mapa e o plano final é contínuo e tem a
mesma duração do áudio.

## Legendas `.ass`

- Fonte `Cinzel`, caixa alta, branco, contorno/sombra legíveis.
- Destaque apenas uma palavra-chave por linha na cor canônica do personagem.
- Use fade da linha inteira; não use varredura `\\k` por padrão.
- Alinhe ao Whisper com timestamps por palavra, mas substitua erros fonéticos pela letra oficial.
- Revise amostras no começo, meio e fim e confira safe area em 1920x1080.

## Render

Use `terminal` para normalizar os planos em 1920x1080, SAR 1:1, 30 fps e H.264. Concatene o
intermediário sem legenda, depois queime o `.ass` e faça duas saídas:

- master: CRF 18, AAC 256 kb/s, `+faststart`;
- WhatsApp: CRF 27–28, AAC 128 kb/s, abaixo de 100 MB, `+faststart`.

Não reutilize uma saída antiga após alterar o mapa temporal; áudio, vídeo e legenda devem nascer da
mesma versão do plano.

## Verificação

- decodificação integral do master e do compacto sem erro;
- duração de áudio/vídeo dentro de 60 ms, 1080p30, H.264/AAC e faststart;
- loudness e true peak medidos, sem clipping;
- auditoria do intermediário a cada 0,5 s sem cards, end screens, marcas ou legendas externas;
- emenda inspecionada em waveform e sequência de frames;
- relatório de sincronia compara distância média dos cortes aos onsets antes/depois;
- arquivo compacto aberto e, quando solicitado, confirmado pela API de envio.

Não declare final apenas porque o render terminou: a entrega está concluída somente depois de todas
as verificações correspondentes ao pedido.
