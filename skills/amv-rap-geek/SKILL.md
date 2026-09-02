---
name: amv-rap-geek
description: "Crie AMVs de rap geek com narrativa e beat precisos."
version: 2.1.0
author: Álvaro (alvaro209890), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [anime, amv, rap-geek, beat-sync, ffmpeg]
    related_skills: [anime-amv-edit]
---

# amv-rap-geek

Guia executável para criação e montagem de videoclipes musicais e AMVs de Rap Geek (estilo RM Raps / MUGEN RAPS) a partir de áudio, transcrição e clipes brutos de anime.

## 1. Estrutura do Projeto

Todo projeto deve residir em `/home/acer/Documentos/Video_Studio/projetos/<slug>/`:
```
projetos/<slug>/
├── audio/<slug>.mp3             # Áudio oficial da música
├── raw/                         # Clipes brutos baixados via yt-dlp (1080p/4K twixtor/animation)
├── cortes/                      # Cenas cortadas e normalizadas
├── legendas/                    # Arquivo .ass de legendas cinematográficas
├── transcricao.json             # Alinhamento Faster-Whisper (palavra por palavra)
└── PROMPT_CODEX_CRIACAO_AMV.md  # Especificação narrativa e de cortes
```

## 2. Regras de Ouro da Produção

1. **Pureza Total do Universo:** Exclusividade aos personagens e cenas canônicas do anime do tributo.
   ⚠️ **Nome de arquivo e título do vídeo não são prova.** Fontes que se anunciam como clipe do
   anime podem ser animação vetorial de fã (`wWi5gVmXfmY` = "Guii Animz Presents") ou compilação
   com outros animes. Audite frame a frame — 1 fps em folha de contato — antes de montar.
2. 🔴 **Zero Marcas d'Água E Zero Legenda de Dublagem:** nenhum clipe sai com marca de canal
   nem com legenda de dublagem de terceiro — só ficam as legendas da MÚSICA (o `.ass`).
   A fonte sai limpa **antes** de entrar na montagem. **Três técnicas, uma só não resolve:**
   - logo pequeno e fixo → `delogo=x=:y=:w=:h=`
   - marca sobre line-art de mangá → `curves=all=0/0 0.60/0.60 0.803/1 1/1` (ponto branco)
   - **legenda de dublagem no rodapé → recorte 16:9 acima dela + zoom** (`crop=1546:870:<x>:0,scale=1920:1080`).
     ⭐ O topo do texto de legenda ficou em **y=885** nas 3 fontes de anime auditadas — comece por aí.
     **Nunca `delogo` em legenda:** a caixa larga deixa borrão horizontal atravessado, pior que a legenda.
   - **texto grande espalhado no quadro (fan-edit) → não tem filtro: RETIMAR o corte** para uma janela limpa.
   Registre as janelas limpas por fonte num dict `JANELAS_LIMPAS` e faça o validador do render
   barrar qualquer corte fora delas **antes** de gastar CPU.
   📄 Receita completa, como medir a linha de corte e o mapa de contaminação das fontes já
   auditadas: `references/limpeza-fontes.md`.
3. **Todo corte novo leva as tarjas de marca.** 🔴 Regra do Álvaro (01/09/2026), no
   padrão dos cortes do Hakari. **Os já postados não são refeitos** — vale de agora em diante.

   | Elemento | Especificação |
   |---|---|
   | Tarja de cima | `drawbox=x=0:y=180:w=1080:h=180:color=black@0.75:t=fill` |
   | Título | ciano `#00ffcc`, `fontsize=48`, `y=210` — ex. `MUGEN RAPS - FEBRE DO JACKPOT` |
   | Subtítulo | branco `#ffffff`, `fontsize=36`, `y=280` — ex. `KINJI HAKARI (JUJUTSU KAISEN)` |
   | Tarja de baixo | `drawbox=x=0:y=1540:w=1080:h=150:color=black@0.75:t=fill` |
   | Assinatura | amarelo `#ffcc00`, `fontsize=34`, `y=1595` — `@MugenRapsOficial` |

   Tudo centralizado (`x=(w-text_w)/2`) com sombra. ⚠️ **Sem emoji nesses textos** — a fonte
   do `drawtext` não desenha e vira quadradinho. Gerador pronto:
   `~/Documentos/Video_Studio/assets/tiktok/gerar_corte_marcado.py`.

4. **Corte vertical (9:16): ENQUADRA, nunca RECORTA.** 🔴 Regra do Álvaro (01/09/2026),
   vale para **TikTok, Reels e Shorts do YouTube**. O frame 16:9 **inteiro** entra centralizado
   sobre um fundo borrado do próprio frame — nunca `crop` no primeiro plano:

   ```
   [0:v]split=2[bg][fg];
   [bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,
       gblur=sigma=35:steps=3,eq=brightness=-0.15[bgb];
   [fg]scale=1080:-2,eq=contrast=1.08:saturation=1.15:brightness=0.02,
       unsharp=5:5:0.8:5:5:0.0[fgs];
   [bgb][fgs]overlay=(W-w)/2:(H-h)/2
   ```

   `scale=1080:-2` (não `-1`): altura par, senão o x264 recusa. Center-crop **decepa o rosto e
   corta as pontas da legenda** — foi exatamente o que aconteceu nos cortes do Kashimo de
   01/09 08:03, que tiveram de ser refeitos. **Confira um frame antes de publicar.**
   Receita canônica: `~/Documentos/Video_Studio/tiktok_cortes/gerar_cortes_antidetect.py`.

   **Publicar o corte:** 📄 `references/publicar-tiktok-cdp.md` — o CDP por one-liner de shell
   travou o Hermes por 1 h em 01/09/2026 (aspas comidas no aninhamento shell→Python→JS) e
   já pôs **dois posts no ar com o nome do arquivo como legenda**. Scripts que funcionam:
   `~/Documentos/Video_Studio/assets/tiktok/` — `postar_tiktok.py <n>` faz **ensaio**
   (sobe, escreve a legenda, tira print e para); com `--publicar` é que clica.

   **Instagram Reels:** 📄 `references/publicar-instagram-reels.md`. Fluxo
   `Criar → Postar → arquivo → Cortar → Avançar ×2 → legenda → Compartilhar`, scripts em
   `~/Documentos/Video_Studio/assets/instagram/`. 🔴 A etapa **Cortar** abre recortada —
   escolha **9:16** no ícone `Selecionar corte` e **confirme medindo o `<video>`**
   (≈ 0,5613), escopando a busca em `div[role="dialog"]`: `document.querySelector('video')`
   pega vídeo **do feed atrás do modal**. Validado com 6 Reels em 01/09/2026.

4. **Vinheta Oficial v2 — obrigatória em vídeo longo, proibida em corte (0.0s a 4.0s):**
   - Arquivo Oficial: `/home/acer/Documentos/Video_Studio/assets/intro/intro_mugen_v2_169_mudo.mp4`.
   - 🔴 **A v1 está aposentada.** `nova_intro_mugen_oficial.mp4` e `intro_canal.mov` **não podem
     mais ser usados**: o emblema central deles era o **logo do BTS** (marca registrada da HYBE),
     herdado de arte gerada por IA. A v2 traz um **torii** original no lugar.
   - 🚫 **Vídeo já publicado fica com a v1.** Decisão do Álvaro (01/09/2026): nada que já
     está no ar é reenviado, substituído ou tem a abertura trocada — nem Muzan, nem Nezuko,
     nem Hakari, nem Kashimo. Republicar custa views, comentários e ranqueamento de um vídeo
     que já performa, e 4 s de abertura não pagam esse preço. **A v2 vale da próxima faixa em
     diante.** O canal conviver com as duas vinhetas é **esperado** — não "corrija" isso.
   - ⭐ **Só vídeo longo (16:9) leva vinheta.** Short, Reel, TikTok e qualquer corte vertical
     entram **direto no conteúdo** — 4 s de marca queimam a retenção justamente onde ela decide
     se o vídeo vive. Se o Álvaro pedir marca no vertical, use o corte de 1,5 s
     `intro_mugen_v2_916_curta_mudo.mp4`.
   - Vídeo mutado na abertura com a música tocando desde o segundo `0.00s`.
   - Corte seco para a animação principal no segundo `4.00s`.
   - Variantes em `assets/intro/`: `169`/`916`, cada uma em `4.0s` e `curta` (1,5 s), cada uma com
     par `_mudo`. Regerar tudo: `assets/intro/scripts/build.sh`.
4. **Abertura Curta, mas com Espaço Narrativo:**
   - Diferencie **fala/monólogo de abertura** da **primeira estrofe cantada**. Preserve uma fala
     icônica e o título quando eles sustentarem a narrativa; a letra não precisa começar logo aos 4 s.
   - Como referência, faça a primeira estrofe cantada entrar em até cerca de **20 s depois da
     vinheta de 4 s**. Esse valor é uma preferência editorial, não uma obrigação para músicas cuja
     construção musical peça outro tempo.
   - Encurte somente silêncio, sintetizador ou beat repetitivo sem nova informação. A emenda deve
     remover um número inteiro de beats/compassos e ser refinada em zero crossing ou microcrossfade,
     sem cortar a cauda da última palavra nem o ataque da próxima.
   - Nunca altere só o áudio. Registre um **mapa de tempo por trechos** e aplique a mesma transformação
     ao áudio, `.ass`, plano visual, referências do Whisper e relatórios de QA. Veja
     `references/sincronia-musical.md`.
5. **Legendas Cinematográficas (.ass):**
   - Fonte: `Cinzel` (romana clássica, CAIXA ALTA, branca).
   - Destaque cinético em palavra-chave com a cor do personagem (ex: Ciano/Ouro para Kashimo, Carmesim `&H001515E8&` para Muzan, Verde Neon `&H00A0F000&` para Hakari).
   - Fade suave de linha inteira sem varredura de karaokê.
   - Sincronização rigorosa milissegundo a milissegundo baseada na transcrição Whisper.
   - O timestamp acompanha a **voz**. O corte visual pode ser aproximado do kick/ataque mais próximo
     sem deslocar a legenda junto.
6. **Corte Narrativo Canônico e Específico (1:1):**
   - As imagens não podem ser apenas conceituais ou genéricas: devem refletir a cena/evento específico mencionado no verso (ex: se fala das Luas Inferiores, usar o massacre do Ep 26; se fala de Yoriichi, usar o corte da Respiração Solar; se fala de Nezuko sob o sol, usar a cena do Ep 11 da S3; se fala de Tanjiro Rei dos Demônios, usar a animação do Tanjiro Demon King).
7. **Formatação de Textos e Bios para Redes Sociais:**
   - Ao fornecer cópias de bio, descrições ou copys curtas para redes sociais (TikTok, Reels, Shorts), enviar sempre em mensagem única e limpa pronta para copiar e colar, sem blocos fragmentados ou texto intermediário desnecessário.
8. **Distribuição e Upload via TikTok Studio:**
   - Conta oficial TikTok: `@mugen_raps` (autenticada via Google `alvaroemanuel642@gmail.com`).
   - Upload automatizado via Chrome CDP na rota `https://www.tiktok.com/tiktokstudio/upload`.
   - **Regra Obrigatória da Descrição no TikTok:** Toda postagem DEVE conter o nome da música, frase de impacto/gancho e chamada explícita para o canal oficial do YouTube com o link (`Assista completo no YouTube: youtube.com/@MugenRapsOficial`).
   - **Estratégia de Cortes (3 Cortes por Faixa):** Para cada rap lançado no YouTube, produzir imediatamente 3 cortes verticais 9:16 (~35s a 45s):
     1. *Abertura & Gancho Inicial* (Fala icônica + Verso 1)
     2. *O Drop do Refrão / Habilidade Principal* (ex: Jackpot, Respiração Solar, Domínio)
     3. *Clímax da Batalha / Duelo* (Trecho de luta intensa e rima rápida)
   - O painel aceita injeção via `DOM.setFileInputFiles`, preenchimento de legendas com hashtags segmentadas (`#mugenraps #rapgeek #animerap`) e clique no botão `Publicar`.
   - **Gotchas do TikTok Web Studio:** Contas novas (primeiras 24-48h de criação) podem ter limite diário rígido anti-spam para publicações via Web Studio (*"Você atingiu o limite de verificações para hoje"*). Nesses casos, o primeiro corte sobe via web e os demais devem ser enviados imediatamente no WhatsApp para postagem manual sem bloqueio pelo app móvel ou agendados para o dia seguinte.
9. **Estratégia de YouTube Shorts para Divulgação do AMV:**
   - **Postagem Simultânea dos 3 Cortes no YouTube Shorts:** Para cada AMV longo/oficial lançado, postar os 3 mesmos cortes no YouTube Shorts via automação no YouTube Studio (`studio.youtube.com/channel/<ID>/videos/upload?d=ud`).
   - **Padrão dos Shorts:**
     - Resolução: 1080x1920 (9:16 vertical com blur nas bordas e ação centralizada).
     - Títulos: Foco no gancho da cena + `#Shorts` + `#Anime` (ex: `#JujutsuKaisen`, `#DemonSlayer`).
     - Descrição Obrigatória: Link direto e clicável para o videoclipe principal completo em 4K (`youtu.be/...`).
     - Metadados: Público `PUBLIC`, não infantil (`VIDEO_MADE_FOR_KIDS_NOT_MFK`).
     - O YouTube Shorts não possui limite diário de conta nova como o TikTok, permitindo publicar todos os 3 cortes no mesmo dia para tracionar o lançamento principal.

## 3. Transcrição & Alinhamento Temporal de Alta Precisão

Leia `references/sincronia-musical.md` antes de encurtar a música ou reajustar cortes ao beat.
Ele define o mapa temporal único, a tolerância para snap visual e as provas mínimas de sincronia.

Utilizar Faster-Whisper local com modelo `medium` ou `small` com `beam_size=5` e `word_timestamps=True` para evitar defasagem rítmica nas legendas:
```python
from faster_whisper import WhisperModel
import json

model = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
segments, _ = model.transcribe(
    "audio/<slug>.mp3",
    language="pt",
    word_timestamps=True,
    beam_size=5
)
data = [{"id": s.id, "start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
         "words": [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)} for w in s.words]}
        for s in segments]
with open("transcricao.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

## 4. Pipeline de Renderização em Duas Vias (Master 1080p + WhatsApp)

1. A vinheta v2 **já sai em 1080p@30fps H.264/yuv420p** — não precisa normalizar; concatene direto. (Só vídeo longo; corte vertical não leva vinheta.)
2. Cortar cada plano com `scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1` e filtros de contraste/saturação.
3. Concatenar com `concat` e muxar com áudio original e legenda `.ass`.
4. Gerar simultaneamente:
   - **Master 1080p (`crf=18`, `b:a=256k`)** para publicação no YouTube.
   - **Versão Otimizada WhatsApp (`crf=26`, `b:a=128k`)** garantindo arquivo < 100MB para envio direto via bridge.
5. ⭐ **Audite o intermediário, não o master.** O passo 3 gera um `temp_video_<versao>.mp4`
   ainda **sem** o `.ass` queimado. É nele que a auditoria de contaminação roda: ali qualquer
   texto na tela é de terceiro, sem chance de confundir com a legenda da música. Só entregue
   depois que essa varredura der zero. Ver `references/limpeza-fontes.md` §5.
6. Valide a música editada e o plano visual com as métricas de
   `references/sincronia-musical.md`: emenda sem clique, grid preservado, primeira voz no tempo
   editorial aprovado, legendas transformadas pelo mesmo mapa e melhora mensurável dos cortes.

7. 🔴 **Meça o true peak antes de entregar — o pipeline estoura sozinho.**
   Auditoria de 01/09/2026: **os quatro AMVs anteriores saíram clipando.**

   | Faixa | LUFS | True peak |
   | :--- | ---: | ---: |
   | Kashimo | −9.08 | **+4.88 dBTP** |
   | Hakari | −9.42 | **+1.12 dBTP** |
   | Muzan V5 intro v2 | −10.31 | **+0.67 dBTP** |
   | Sukuna (antes da correção) | −9.43 | **+0.86 dBTP** |

   A causa não é a edição: o master do Suno já chega em **+0.55 dBTP** e o
   encoder AAC ainda **acrescenta** overshoot — quanto menor o bitrate, pior
   (medido: +0.55 dB a 320k, +2.10 dB a 128k). Muxar o mp3 direto, como o
   pipeline fazia, carrega o estouro para o arquivo final.

   Receita validada no Sukuna (não reencoda o vídeo, só a trilha):

   ```bash
   # 1) limita em oversampling 4x — pega o pico intersample, não só o sample
   ffmpeg -i audio/<faixa>.mp3      -af "aresample=192000:resampler=soxr,          alimiter=limit=0.7674:attack=5:release=60:level=0,          aresample=48000:resampler=soxr"      -c:a pcm_s24le render/audio_tp.wav          # limit 0.7674 = −2.3 dBFS

   # 2) AAC com bitrate ALTO nas duas vias (a do WhatsApp também: 256k)
   ffmpeg -i render/audio_tp.wav -c:a aac -b:a 320k -ar 48000 render/a_master.m4a
   ffmpeg -i render/audio_tp.wav -c:a aac -b:a 256k -ar 48000 render/a_whats.m4a

   # 3) remux sem tocar na imagem
   ffmpeg -i saidas/<master>.mp4 -i render/a_master.m4a      -map 0:v:0 -map 1:a:0 -c:v copy -c:a copy -movflags +faststart -shortest      saidas/<master>_tpfix.mp4

   # 4) confirme: I entre −10 e −11 LUFS, TP ≤ −1.0 dBTP
   ffmpeg -i saidas/<master>_tpfix.mp4      -af "loudnorm=I=-14:TP=-1:LRA=11:print_format=json" -f null -
   ```

   Não baixe o bitrate do áudio do WhatsApp para "caber": o arquivo é dominado
   pelo vídeo (o do Sukuna ficou em 56 MB com AAC 256k) e 128k só devolve o
   clipping. Alvo de entrega: **−10 a −11 LUFS, TP ≤ −1.0 dBTP**.

   ⚠️ Kashimo, Hakari e Muzan **já estão no ar com o áudio estourado**. A
   correção é remux (passo 3) sem republicar o vídeo — decisão do Álvaro
   pendente sobre substituir os arquivos publicados.

## 5. Estado das faixas

| Faixa | Versão final | Arquivo |
| :--- | :--- | :--- |
| **Muzan Kibutsuji** | **V5 intro v2 (01/09/2026) — PUBLICADA** | `saidas/muzan_amv_v5_introv2_1080p.mp4` |
| **Sangue Explosivo — Nezuko** | **V2 (01/09/2026) — FINAL** | `projetos/sangue-explosivo/saidas/sangue_explosivo_nezuko_amv_v2_master_1080p.mp4` |
| **Ryomen Sukuna — O Rei das Maldições** | **Master 01/09/2026 — FECHADO, não publicado** | `saidas/sukuna_amv_oficial_master_1080p.mp4` |

⚠️ **Muzan está fechado e publicado.** O que foi ao ar em 01/09/2026 é a **V5 com a
intro v2** (`saidas/muzan_amv_v5_introv2_1080p.mp4`, 3:56) — não a V4. Não voltar para
V1/V2/V3: elas têm `Subscribe`, `4KAnime`, `4K ANINOMI`, cartelas `UPPER FIVE/FOUR/ONE`
e legendas em inglês/português queimadas. Pendência conhecida: `tanjiro_demon_king`
(203–214 s) é animação de fã, não o anime — trocar numa próxima rodada.

## 6. Publicação — skill separada

Montar não é entregar. Para subir nas plataformas, use a skill
**`publicar-canal-mugen`** (ferramenta única:
`~/Documentos/Video_Studio/ferramentas/publicar.py`).

🔴 **Todo vídeo do YouTube sai com capa própria** (ordem do Álvaro, 01/09/2026).
Publicar e deixar a miniatura automática não conta como entregue. A capa é
1280×720, feita de **frame real do próprio vídeo** — nunca arte de IA — e o
gerador de referência é `ferramentas/artes_muzan.py`.

**Confira quem está no frame.** A primeira capa do Muzan usou um frame de Lua
Superior (cabelo branco, olhos dourados com kanji) achando que era ele. Muzan
tem cabelo escuro e olho **vermelho**; olho com kanji nunca é ele.

Dois geradores servem de modelo: `ferramentas/artes_muzan.py` e
`ferramentas/artes_sukuna.py` (este importa as funções daquele — reaproveite em
vez de duplicar). A composição que funciona é sempre a mesma: personagem de um
lado, coluna de texto do outro, scrim escuro por baixo do texto, nada no canto
inferior direito (selo de duração) e conferência no card de 210 px.

**Tire o frame do picture lock, não do master.** O `render/<slug>_picture_lock_
sem_legenda.mp4` ainda não tem o `.ass` queimado, então não é preciso recortar
faixa de legenda antes de enquadrar — foi o remendo que a capa do Muzan exigiu.

**Identidade por faixa:** Sukuna encarnado tem marca em losango na testa, duas
listras pretas sob **cada** olho, listras no queixo e olho vermelho. Frame do
Yuji sem essas marcas é o Yuji, não o Sukuna.


## 7. Lançamento: ordem, copy e leitura de métrica

📄 `references/lancamento-e-copy.md` *(01/09/2026)* — o que a auditoria dos
números públicos do canal mostrou e o que virou regra.

🔴 **O longo sobe primeiro, os cortes 2 a 4 h depois.** Conversão Short→longo:
Hakari (longo 4 h antes) **5,1%** · Kashimo (juntos) 1,0% · Muzan (cortes
antes) 0,8%.

🔴 **Nenhum longo sobe sem descrição completa e 12–16 tags.** O Muzan saiu com
0 tags e 402 caracteres porque o `publicar.py` não tinha `--tags` — agora tem.

🔴 **A copy do corte manda para o VÍDEO, não para o canal.** Hoje os cortes
apontam para `@MugenRapsOficial`; o certo é `youtu.be/<ID_DO_LONGO>`.

🔴 **Métrica se lê por idade, nunca por total bruto.** Os cortes do Muzan
pareciam fracos e eram o lote mais rápido do canal — só tinham 2 h de vida.

⚠️ **A música não costuma ser o problema.** O Muzan tem a maior taxa de like
do canal (40%) e a menor view: isso é distribuição, não faixa.

### Muzan — o que está no ar (01/09/2026)

| Onde | Link / id |
| :--- | :--- |
| YouTube (AMV 3:56) | `kHzEpNzJqCI` — youtu.be/kHzEpNzJqCI |
| YouTube Shorts | `ue_kcuHPDak` · `rtn800PkISI` · `P4mkxtqRq7E` |
| TikTok @mugen_raps | 3 cortes |
| Instagram @mugenraps_oficial | `DcwEs0uNHyS` · `DcwNaL6tqSx` · `DcwN_LVtzDo` |
| Artes | `saidas/muzan_capa_youtube.jpg`, `muzan_banner_canal.jpg`, `muzan_capa_streaming_3000.jpg` |
