# Plano — Skills de vídeo no **Hermes** 🥇

**Princípio:** 🔒 **autonomia total.** O Hermes executa o pipeline inteiro — download, transcrição, extração de frames, **análise visual com a própria ferramenta de visão**, roteiro, geração de cenas, narração, edição, exportação e dublagem — **sozinho**, e entrega no WhatsApp. **Zero roteamento para outro agente.** Quando precisa paralelizar, usa **subagentes internos** dele mesmo (`delegation` / `moa`).
**Canal:** ⭐ **WhatsApp** (também Discord e web chat). É por lá que a skill opera, recebe ordens e entrega resultado.
**Status (atualizado em 2026-08-10):** planejamento original + execução local parcial validada.
📖 Contexto comum: [`README.md`](README.md).

> **Estado executável:** `video-analise` já mede cortes/BPM/LUFS e gera contato;
> `video-criacao` entregou o Gojo v3 completo e validado; `video-dublagem` já encaixa segmentos
> com Rubber Band/QA, mas a separação/remix integral continua bloqueada sem Demucs. A operação
> ponta a ponta pelo WhatsApp e a aprovação humana dos três eixos ainda não ocorreram; o gate
> continua aberto. Os checkboxes abaixo preservam o plano original e não anulam esse estado.

---

## 🚦 ORDEM DE EXECUÇÃO / GATE

> ## **ESTE É O AGENTE DA FASE 1. COMEÇA AQUI.**
>
> | | |
> |---|---|
> | **Fase** | **1 — AGORA** |
> | **Bloqueado por** | nada |
> | **Bloqueia** | `PLANO_CLAUDE_CODE.md`, `PLANO_CURSOR.md`, `PLANO_OPENCODE.md`, `PLANO_CODEX.md` |
>
> **A skill de vídeo do Hermes é desenvolvida, testada e validada 100% antes de qualquer outro agente começar.** Os três eixos — **analisar**, **criar** e **dublar** — precisam estar funcionando **pelo WhatsApp, com o Álvaro**, ponta a ponta.
>
> **Nada de dividir esforço.** Enquanto este documento não estiver com todos os itens da **§6 — Critérios de validação** marcados e aprovados pelo Álvaro no WhatsApp, os outros quatro planos ficam **congelados**.
>
> **Por que o Hermes primeiro:** é o único agente que já está no bolso do Álvaro. O caso de ouro — *"vi um Reel no celular, mandei o link, o vídeo chegou pronto"* — só existe aqui. Os outros quatro são conveniências de terminal; este é o produto.

---

## 0. O canal é o WhatsApp — e isso desenha a skill

Uma skill de vídeo no terminal pode imprimir 400 linhas, abrir um preview e esperar `Ctrl+C`. **No WhatsApp nada disso existe.** O que existe:

- mensagens curtas, cortadas em **4.096 caracteres**;
- arquivos entregues como **anexo nativo** (vídeo toca dentro do chat);
- o Álvaro **saindo do chat** e voltando 40 minutos depois;
- perguntas que precisam de resposta — em **texto, áudio, print ou vídeo**.

A skill é, antes de tudo, **um protocolo de conversa**. O `ffmpeg` é a parte fácil.

### 0.1 O que o Hermes tem no toolset `whatsapp` (verificado em `~/.hermes/config.yaml`)

| Necessidade do pipeline | Ferramenta nativa | Estado verificado |
|---|---|---|
| **Ver imagem / keyframe** | `vision` (`vision_analyze`) | `auxiliary.vision` → provider **`groq`**, modelo `meta-llama/llama-4-scout-17b-16e-instruct`, timeout 120 s ✅ |
| **Rodar yt-dlp, ffmpeg, whisper** | `terminal` + `code_execution` | ✅ (`security.allow_lazy_installs: true`) |
| **Site com login (Instagram)** | `browser` | ✅ no toolset `whatsapp` |
| **Narração / dublagem** | `tts` (`text_to_speech`) | provider **`edge`**, voz **`pt-BR-FranciscaNeural`** ✅ — devolve caminho `MEDIA:` |
| **Perguntar e esperar resposta** | `clarify` | ✅ até 4 opções + "Outro"; `agent.clarify_timeout: 1800` (30 min) |
| **Gerar imagem de cena** | `image_gen` | ⚠️ tool presente, **sem credencial** — ver §5, gotcha nº 1 |
| **Paralelizar** | `delegation` / `moa` | ✅ `max_concurrent_children: 3`, `subagent_auto_approve: true` |
| **Entregar arquivo** | `MEDIA:<caminho>` | ✅ vídeo/imagem/áudio/documento como anexo nativo, com legenda |
| **Memória e fila** | `memory`, `todo`, `session_search`, `kanban.db` | ✅ |
| **Ler o que já leu** | `audio_cache/`, `image_cache/`, `cache/vision/` | ✅ evita re-síntese e re-análise |

**Correção de uma versão anterior deste plano:** estava escrito que *"o Hermes não analisa keyframes sozinho — ele roteia essa etapa"*. **Isso está errado e foi removido.** O bloco `auxiliary.vision` existe e está configurado, e a tool `vision` está no toolset `whatsapp`. O Hermes enxerga por conta própria.

### 0.2 O que **não** está no toolset `whatsapp` (verificado)

| Ausente no WhatsApp | Onde existe | Consequência para a skill |
|---|---|---|
| `video_gen` | só no toolset `cli` | Cena animada por IA não sai de um pedido no WhatsApp. Caminho padrão: `image_gen` + `zoompan` (Ken Burns) — que resolve ~80 % do Modo A e custa zero |
| `computer_use` | só no toolset `cli` | Automação de GUI fica fora; o `browser` cobre o caso do Instagram |
| `cronjob` | nem em `cli` nem em `whatsapp` | Agendamento vai por `hermes cron` via `terminal` — e roda em **sessão nova, sem o contexto do chat** |

Peças vizinhas reaproveitáveis em `~/.hermes/skills/`: `creative/songwriting-and-ai-music` (parente direto do Modo B), `creative/comfyui`, `creative/manim-video`.

---

## 1. Skills a criar

```
~/.hermes/skills/
├── video-analise/
│   ├── SKILL.md
│   ├── scripts/          ← arquivos .sh/.py (NÃO heredoc — ver §5, gotcha nº 3)
│   └── references/protocolo-whatsapp.md · rubrica.md · plataformas.md
├── video-criacao/
│   ├── SKILL.md
│   ├── scripts/
│   └── references/formulas-roteiro.md · presets-identidade.md · specs-export.md
└── video-dublagem/
    ├── SKILL.md
    ├── scripts/
    └── references/sincronia.md
```

`references/protocolo-whatsapp.md` é **compartilhado pelas três** e contém o que está na §2 — o protocolo de conversa é a parte que não pode divergir entre skills.

---

## 2. ⭐ Protocolo de conversa no WhatsApp

Esta seção é o núcleo do plano. As três skills obedecem a ela.

### 2.1 Entradas aceitas — o Álvaro manda, o Hermes entende

| O que o Álvaro manda | Como chega ao Hermes (verificado) | O que a skill faz |
|---|---|---|
| **Link** (YouTube, Reels, Shorts, TikTok) | texto na mensagem | detecta a URL → confirma intenção → dispara análise |
| **Vídeo** (arquivo/encaminhado) | bridge salva em `~/.hermes/cache/videos/`, o **caminho absoluto** chega ao agente | **pula o download inteiro** — vai direto para áudio/transcrição/frames |
| **Print / imagem** | `~/.hermes/cache/images/` | `vision_analyze` → referência visual ("quero legenda assim") |
| **Áudio / nota de voz** | ⚠️ **transcrito automaticamente** pelo STT (`stt.provider: local`, `model: base`) — o agente recebe **texto** | pedido falado. Para usar como **referência de timbre**, a skill precisa pegar o `.ogg` em `~/.hermes/audio_cache/` pelo `terminal` — o texto não basta |
| **Documento** (`.md`, `.txt`, roteiro) | conteúdo injetado inline (até 100 KB) | roteiro pronto → pula direto para produção |
| **Texto** | mensagem | briefing, ajuste, resposta a pergunta |

**Regra de disparo.** Link solto **não** dispara o pipeline (download + Demucs + Whisper custam minutos, disco e API). O Hermes responde curto e pergunta. Exceção: a mensagem já traz a intenção — *"analisa esse"*, *"faz um igual"*, *"dubla pra inglês"*.

**Debounce.** O adaptador junta mensagens em rajada (**5 s**, 10 s para fragmentos longos) numa única chamada. Então *link* + *"faz um igual"* mandados separados **chegam juntos**. Consequência prática: **não responder duas vezes** ao que é uma ordem só.

### 2.2 Saídas — o que o Hermes devolve

| Entrega | Forma | Quando |
|---|---|---|
| **Aceite** | texto curto, ≤2 linhas | em segundos, sempre |
| **Progresso** | texto curto por marco | jobs acima de ~2 min |
| **Pergunta** | `clarify` (lista numerada) | nos pontos ⏸️ do fluxo |
| **Resumo da análise** | texto no chat, **≤8 linhas** | ao terminar a análise |
| **`ANALISE.md` completo** | `[[as_document]] MEDIA:/caminho/ANALISE.md` | junto do resumo |
| **Keyframes** | `MEDIA:` (imagem nativa) | 2–3 frames que sustentam o veredito |
| **Vídeo final** | `MEDIA:/…/final_9x16.mp4` **+ legenda** | toca dentro do chat |
| **Narração isolada** | `MEDIA:` áudio | quando o Álvaro quer só a voz |
| **Arquivo grande** | link (tunnel/`cursar.space`) | acima de ~16 MB — ver §5, gotcha nº 9 |

**O chat não é lugar de relatório.** O resumo cabe numa tela de celular; o `.md` é o artefato. Relatório longo jogado no chat vira 6 mensagens picotadas em 4.096 caracteres e ninguém lê.

### 2.3 ⏸️ Perguntar e aguardar — o passo que a skill precisa ter marcado

A tool **`clarify`** é o mecanismo. Comportamento verificado:

- **até 4 opções** + uma 5ª automática, "Outro" (resposta livre);
- em plataforma de mensagem, as opções viram **lista numerada** — o Álvaro responde "2";
- se omitir `choices`, a pergunta é **aberta** (texto livre);
- **regra da tool:** *nunca* enumerar as opções dentro do texto da pergunta — elas vão no campo `choices`. Pergunta com "1) … 2) …" escrito no texto renderiza duplicado;
- **timeout: 1.800 s (30 min)**, de `agent.clarify_timeout`.

**Orçamento de perguntas: no máximo 3 por vídeo.** O resto é **default declarado** — o Hermes anuncia o que vai fazer e segue: *"vou de 9:16, 30 s, voz Francisca, estilo jjk-dark — só falar se quiser diferente."* Perguntar demais é pior que errar o preset; o Álvaro está no celular.

**Onde o fluxo pergunta (marcado com ⏸️ nas seções seguintes):**

| ⏸️ Momento | Pergunta típica | `choices` |
|---|---|---|
| Antes de gastar | *"Analiso esse Reel? Uns 4 min."* | `["Analisa", "Só o roteiro", "Depois"]` |
| Estilo | *"Qual estilo?"* | `["Igual ao @silv.mind", "Igual ao RM RAPS", "Outro que eu já analisei"]` |
| Duração / formato | *"Quanto tempo?"* | `["15s", "30s", "45s", "Sem limite"]` |
| Voz e tom | *"Qual voz?"* | `["Francisca (padrão)", "Antônio (masc.)", "Mais séria", "Mais irônica"]` |
| Idioma (dublagem) | *"Pra qual idioma?"* | `["Inglês", "Espanhol", "Os dois", "Outro"]` |
| **Custo / tempo** | *"Esse render usa API paga (~US$ X) e leva ~Y min. Sigo?"* | `["Segue", "Faz a versão barata", "Cancela"]` |
| Aprovação do roteiro | *"Roteiro pronto (colado acima). Renderizo?"* | `["Renderiza", "Encurta", "Refaz o gancho"]` |
| Trocadilho intraduzível | *"'Você Que Sabe' não tem equivalente em inglês. Qual caminho?"* | `["Adaptação livre", "Mantém em pt", "Legenda explicando"]` |

**Se o timeout de 30 min estourar:** o Hermes **não** advinha e **não** cancela em silêncio. Ele grava o estado no `kanban.db`, manda *"fiquei sem resposta; parei em <etapa>, é só falar 'continua'"*, e encerra o turno. Retomada por `session_search`/`memory`.

**Aprovação de texto antes de render** é a regra que mais economiza: texto é barato de revisar, render não é.

### 2.4 Job longo — progresso sem travar o chat

Pipeline de vídeo estoura qualquer expectativa de resposta imediata. Desenho:

1. O trabalho pesado roda como **processo em background** (`terminal`), não como sequência de tool calls. Limites reais: `agent.max_turns: 150`, `gateway_timeout: 3600 s`, aviso em `1200 s`.
2. O script em background **avisa sozinho** a cada marco, por CLI:
   ```
   hermes send --to whatsapp "🎬 transcrito (2:14 de áudio) — vendo os frames agora"
   ```
   Isso funciona **fora** do turno do agente: o Álvaro recebe mesmo com o Hermes ocioso.
3. Marcos padrão (não mais que estes — notificação demais vira spam):
   `baixado` → `transcrito` → `vi os frames` → `roteiro pronto` (⏸️ aprovação) → `renderizando` → `pronto`.
4. O job entra no `kanban.db` com slug e chat de origem, e responde a *"como tá aquele vídeo?"* a qualquer momento.
5. **Indicador de tool.** O WhatsApp já mostra em tempo real qual ferramenta está rodando — de graça, sem configurar. Não é preciso narrar cada passo por texto.

---

# SKILL 1 — `video-analise`

## 1.1 Objetivo

Receber um link (ou um vídeo mandado no chat) e devolver, **sozinho e de forma assíncrona**, um `ANALISE.md` completo — incluindo o eixo visual, lido pela própria tool `vision` — mais um resumo curto no chat.

## 1.2 Quando usar (gatilhos)

- **qualquer URL** de `youtu.be`, `youtube.com/shorts`, `instagram.com/reel`, `tiktok.com`
- **vídeo enviado como arquivo** no chat
- "analisa esse aqui", "olha esse reel", "que estilo é esse", "por que esse vídeo foi bem"
- "extrai o roteiro desse vídeo"
- link + "quero fazer igual" → encadeia direto na `video-criacao`

## 1.3 Fluxo passo a passo — tudo dentro do Hermes

**0. `doctor` próprio.** Via `terminal`: versão do `yt-dlp` (rejeitar a do apt — README §3.4), `ffmpeg`, `faster-whisper`, `Demucs`, `PySceneDetect`, disco livre, e um *ping* na tool `vision`. Falhou algo → dizer **antes** de começar, não no meio.

**1. ⏸️ Confirmar** (salvo intenção explícita): `clarify` — *"Analiso esse Reel? Uns 4 min."*

**2. Aceite imediato** (segundos): *"Peguei. Baixando e transcrevendo — te aviso em ~4 min."* Silêncio de 6 minutos no WhatsApp parece travamento.

**3. Enfileirar** em `kanban.db`/`processes.json`, com slug e chat de origem.

**4. Obter o vídeo.**
- Veio como **arquivo no chat** → já está em `~/.hermes/cache/videos/`; **pular esta etapa**.
- Veio como **link** → `terminal` → `yt-dlp`.
- Deu `login required` (Instagram) → **o próprio Hermes abre a tool `browser`**, carrega o Reel na sessão logada e captura o arquivo. Nunca "não consegui".

**5. Áudio e faixas** — `ffmpeg` extrai `audio.wav`; `Demucs` separa `vocals.wav` + `music.wav`. Isso já responde *tem narração?* e *tem trilha?*.

**6. Transcrição** — `faster-whisper` (`medium` no dia a dia, `large-v3` no passe final) + alinhamento por palavra, sobre `vocals.wav` quando há música.
⚠️ **Não usar a legenda do YouTube:** `timedtext` devolve 0 byte mesmo listando a trilha `pt/asr`.
⚠️ **Não confundir com o STT do chat:** a nota de voz do Álvaro é transcrita pelo modelo `base` (rápido, fraco); a análise usa `medium`/`large-v3`.

**7. Cortes e ritmo** — `PySceneDetect` → `cenas.csv`; cortes/min, média e mediana de plano, desvio. No Modo B: BPM (`librosa`) e **% de cortes na batida** (±80 ms).

**8. Extração de frames** — `ffmpeg`, 1 keyframe por plano, limitado a ~15 representativos.

**9. 👁️ Análise visual — a tool `vision`, aqui, dentro do Hermes.**
Keyframes em lotes para `vision_analyze` (Groq `llama-4-scout`) com prompt fixo pedindo, **de uma vez só**: paleta dominante, enquadramento, tipo de material (clipe de anime / arte estática / gameplay / talking head), **estilo de legenda** (fonte, peso, contorno, posição, se é karaokê), overlays e efeitos.
Operacional: lotes pequenos (timeout 120 s), cache por hash em `image_cache/`, e paralelização por **`delegation`** — **até 3** subagentes internos simultâneos (`max_concurrent_children: 3`), sem sair do Hermes.
⚠️ Como o modelo de chat é texto-only (DeepSeek), o `vision_analyze` devolve **descrição em texto**, não pixels. **Uma pergunta nova sobre o mesmo frame custa uma chamada nova** — por isso o prompt pede tudo de uma vez.

**10. Áudio: mixagem** — `loudnorm` (análise) → LUFS, faixa dinâmica, pico; medir ducking; estimar se a voz é humana, TTS ou processada por IA.

**11. Consolidar `ANALISE.md`** pela rubrica do README: veredito, estrutura com `[mm:ss]`, roteiro, ritmo, estilo visual, transições, legendas, áudio, **fórmula extraída** e rascunho de `videospec.json`.

**12. Entregar em duas camadas:**
```
resumo ≤8 linhas no chat
[[as_document]] MEDIA:/…/refs/<slug>/ANALISE.md
MEDIA:/…/keyframes/00m03s.jpg   (2–3 frames que sustentam o veredito)
```

**13. Oferecer o próximo passo:** *"quer um no mesmo estilo?"* — encadeia na `video-criacao` sem briefing novo.

**Regra de qualidade:** toda afirmação de estilo precisa de **timestamp** ou **número**. "Edição dinâmica" é proibido; "34 cortes/min, mediana de 1,8 s por plano" é o padrão.

## 1.4 Ferramentas necessárias

**Do Hermes:** `terminal`, `code_execution`, `browser`, `vision`, `file`, `clarify`, `delegation`/`moa`, `memory`, `todo`, `skills`, `hermes-whatsapp`.
**Do sistema (instaladas pelo próprio Hermes via `terminal`):** `yt-dlp` novo (`uv tool install`), `ffmpeg` (já vem no `hermes postinstall`), `faster-whisper`, `WhisperX`, `Demucs`, `PySceneDetect`, `librosa`.

## 1.5 Limitações

- **Visão depende da Groq.** Se `GROQ_API_KEY` falhar, o eixo visual cai — mitigar com fallback interno e **dizer que a análise saiu incompleta**, nunca fingir.
- **Recursos compartilhados.** Whisper e Demucs competem com gateway, WhatsApp e Postgres na mesma máquina: **um job pesado por vez**.
- **Normalizar URL:** links do Instagram vêm com `?igsh=…`.
- **Timeout de 120 s da visão** limita o tamanho do lote de frames.

## 1.6 Próximos passos

1. Escrever o `SKILL.md` com a chamada de `vision` já parametrizada (prompt fixo + tamanho de lote).
2. Testar `browser` num Reel real e gravar a receita em `memories/`.
3. Medir o tempo de um link do WhatsApp até o `ANALISE.md` entregue.

---

# SKILL 2 — `video-criacao`

## 2.1 Objetivo

Produzir o vídeo **inteiro** a partir de um pedido no chat — roteiro, cenas, narração, edição, export 9:16 e 16:9 — e **entregar o arquivo no WhatsApp**.

## 2.2 Quando usar (gatilhos)

- "faz um reel sobre <tema>"
- "cria um short de 30s explicando <coisa>"
- "monta um vídeo no estilo do <slug analisado>"
- "transforma esse áudio/texto em vídeo" (nota de voz ou documento no chat)
- por `hermes cron`: pauta semanal recorrente

## 2.3 Fluxo passo a passo

1. **⏸️ Briefing por `clarify`** — no máximo 2 perguntas (estilo e duração). O resto é preset declarado.
2. **Roteiro** pela fórmula do Modo A (README §3.2), a ~**2,7 palavras/segundo** em pt-BR. Reel de 30 s ≈ 80 palavras.
3. **⏸️ Aprovação do roteiro no chat.** Cola o roteiro (cabe em 4.096 caracteres) e `clarify`: `["Renderiza", "Encurta", "Refaz o gancho"]`.
4. **`videospec.json`** preenchido a partir do preset.
5. **Cenas visuais**, por ordem de custo:
   1. **material próprio/licenciado** (`file`) — hoje o caminho principal (§5, gotcha nº 1);
   2. **`image_gen` + `zoompan`** (Ken Burns) — resolve ~80 % do Modo A **assim que houver credencial**;
   3. `video_gen` **não existe no WhatsApp** — se for indispensável, ⏸️ avisar e rodar em contexto `cli`;
   4. clipe de anime como último recurso (README §9.1).
6. **⏸️ Aviso de custo/tempo** antes de qualquer chamada paga: *"~US$ X e ~Y min. Sigo?"*.
7. **Narração — tool `tts`**: `edge` com `pt-BR-FranciscaNeural`, um arquivo por cena, `audio_cache/` evitando re-síntese.
8. **Legendas** transcrevendo a **narração sintetizada** (não o roteiro — o TTS muda a duração real) → `.ass` karaokê dentro da safe area.
9. **Edição** via `terminal`/`ffmpeg`: `concat` → transições → `ass` → mix com ducking → `loudnorm` −14 LUFS. Encode com **VAAPI** (`h264_vaapi`).
10. **Export** 9:16 principal + 16:9 (reenquadramento, não *letterbox*).
11. **👁️ Autoverificação visual:** 4–6 keyframes do render passam pela tool `vision`: a legenda está cortada? dentro da safe area? o texto está legível sobre o fundo? — **o Hermes revisa o próprio trabalho**.
12. **Entrega:**
    ```
    MEDIA:/…/render/final_9x16.mp4
    legenda: <texto sugerido do post> + hashtags do spec
    ```
    Acima de ~16 MB → link. Se o Álvaro pedir "manda o arquivo original", `[[as_document]]` evita recompressão do WhatsApp.
13. **⏸️ Feedback:** `["Tá bom", "Refaz a narração", "Muda o corte final"]` — e o ciclo reabre sem briefing novo.

## 2.4 Como o Hermes executaria

O diferencial é o **ciclo conversacional**: pedido por voz → roteiro no chat → ajuste → render → arquivo entregue. O Álvaro **nunca abre terminal**. Cada etapa aprovada fica no kanban, então dá para retomar dias depois.

`hermes cron` habilita o modo mais valioso: **pauta automática** — toda segunda, 3 ideias no estilo do `@silv.mind`; o Álvaro responde "faz a 2"; o vídeo chega pronto. ⚠️ Cron roda em **sessão nova sem o contexto do chat** e com `approvals.cron_mode: deny` — o job precisa ser autossuficiente e não pode depender de aprovação interativa.

## 2.5 Limitações

- **Sem credencial de imagem generativa hoje** (§5, gotcha nº 1) — é o bloqueio nº 1 desta skill.
- **`video_gen` ausente no WhatsApp** — decidir entre acrescentar ao toolset ou assumir `image_gen` + `zoompan` como padrão.
- **Render pesado compete com os serviços do Hermes** → fila, um por vez.
- **Autoverificação visual não substitui o olho do Álvaro** — pega erro objetivo (legenda cortada, texto ilegível), não gosto.
- **Modo B completo** (clipe de 4 min com voz IA) exige guia de voz humana e mixagem — o Hermes monta tudo, mas a etapa vocal segue o pipeline "entrada humana + IA" do RM RAPS.

## 2.6 Próximos passos

1. Definir presets padrão para não perguntar nada além do tema.
2. Resolver credencial de imagem (`FAL_KEY` ou `XAI_API_KEY`) **ou** montar a biblioteca de material próprio.
3. Piloto: pedido por WhatsApp → Reel entregue, medindo tempo, custo e nº de perguntas feitas.

---

# SKILL 3 — `video-dublagem`

## 3.1 Objetivo

Dublar sozinho, preservando trilha e sincronia — inclusive vídeos de terceiros que o Álvaro quer em português.

## 3.2 Quando usar (gatilhos)

- "dubla isso pra inglês/espanhol"
- "põe em português" + link ou arquivo
- "quero esse reel em 3 idiomas"
- vídeo em idioma estrangeiro chegando no chat → **oferecer** dublagem

## 3.3 Fluxo passo a passo

1. **⏸️ Confirmar idioma e voz antes de gastar** — é o pipeline mais caro. `clarify`: `["Inglês", "Espanhol", "Os dois", "Outro"]`.
2. **Separar** com `Demucs` → `vocals.wav` + `music.wav`. A trilha original é preservada.
3. **Transcrever** `vocals.wav` com timestamp por palavra.
4. **Segmentar por unidade de fala** (pausa >200 ms), não por frase gramatical.
5. **Traduzir com restrição de duração** — com o **modelo do próprio Hermes** (`deepseek-v4-pro`): cada segmento recebe o orçamento de caracteres do idioma alvo, e pede-se **3 variantes** (curta/média/longa) para escolher no encaixe.
6. **TTS por segmento — tool `tts`**, voz equivalente no idioma alvo (edge tem vozes multi-idioma; ElevenLabs exigiria credencial — §5).
7. **Encaixe temporal, em cascata:** (a) escolher a variante que encaixa; (b) absorver no silêncio adjacente; (c) `rubberband` até **±10 %**; (d) nova tradução mais curta; (e) marcar para revisão.
8. **Remix:** narração + `music.wav` com ducking → `loudnorm`.
9. **Legendas** no idioma novo, geradas do áudio dublado **real**.
10. **QA numérico:** desvio por segmento, média, p95, pior caso. Meta **≤150 ms**. No chat: *"pronto — desvio médio 90 ms, pior 210 ms em [00:14]"*.
11. **⏸️ Trocadilho intraduzível vira pergunta**, não invenção silenciosa. "Você Que Sabe" não tem equivalente direto em inglês.
12. **Entrega incremental:** manda o inglês assim que sai, sem esperar o espanhol.

## 3.4 Ferramentas necessárias

**Do Hermes:** `tts` (multi-idioma), modelo próprio para tradução, `terminal`, `code_execution`, `delegation` (um subagente interno por idioma, até 3), `clarify`, `file`.
**Do sistema:** `Demucs`, `faster-whisper`/`WhisperX`, `rubberband-cli`, `ffmpeg`.
⚠️ **Licenças:** XTTS-v2 é CPML (não comercial); voz clonada de pessoa real exige autorização. Gravar motor e licença na saída.

## 3.5 Limitações

- **Demucs em CPU compartilhada é lento** (~5–10× tempo real); clipe de 4 min derruba a responsividade do Hermes → agendar fora do horário de uso e **avisar o tempo estimado antes**.
- **Sem lip-sync** — irrelevante para narração em off e anime edit; bloqueante para talking head em close, e a skill deve avisar.
- **Prosódia:** TTS não reproduz ironia, e o tom das referências **é** irônico.
- **O Hermes não ouve o resultado** — o QA é numérico; a aprovação final é humana, no chat.

## 3.6 Próximos passos

1. Testar as vozes en/es do `edge` e escolher as padrão.
2. Piloto pt→en de um Reel, entregue no WhatsApp com a tabela de QA.
3. Definir a política de trocadilhos uma vez e gravar em `memories/`.

---

## 4. Autonomia — o que o Hermes faz sem sair de casa

| Etapa | Antes (versão anterior, **descartada**) | Agora |
|---|---|---|
| Análise visual de keyframes | ~~roteava para outro agente~~ | tool **`vision`** (Groq `llama-4-scout`), com cache e lotes |
| Instagram com login | ~~pedia ao Claude Code~~ | tool **`browser`** na sessão logada |
| Julgamento do render | ~~pedia revisão externa~~ | autoverificação por **`vision`** nos keyframes do render |
| Lote / paralelismo | ~~mandava para o OpenCode~~ | **`delegation`** / `moa` — subagentes **internos**, até 3 |
| Ferramentas quebradas | ~~esperava outro agente consertar~~ | `terminal` + `code_execution` consertam na hora |
| Identidade visual | ~~vinha pronta de fora~~ | presets próprios em `references/presets-identidade.md` |

**Fica valendo:** o Hermes pode **abrir** um `ANALISE.md` ou um `videospec.json` produzido em outro ambiente, porque o formato é comum (README §5) — mas **nunca precisa** que outro agente tenha rodado antes.

---

## 5. ⚠️ Gotchas verificados do ambiente Hermes

Descobertos lendo `~/.hermes/config.yaml`, `.env` e o código do adaptador do WhatsApp. Cada um custa horas se for redescoberto na implementação.

1. **🔴 `image_gen` e `video_gen` não têm credencial.** O `.env` tem apenas `DEEPSEEK_API_KEY` e `GROQ_API_KEY` — **não há** `FAL_KEY`, `XAI_API_KEY` nem `DEEPINFRA_*`, e não existe seção `image_gen:`/`video_gen:` no config. As tools aparecem, mas não geram nada. **É o bloqueio nº 1 da Fase 1:** ou se acrescenta uma credencial, ou o Modo A sai de material próprio + `zoompan`.
2. **`video_gen` e `computer_use` não estão no toolset `whatsapp`** (só no `cli`). Verificado em `platform_toolsets`.
3. **🔴 Heredoc dispara aprovação.** `approvals.mode: manual` com `timeout: 60`, e o `command_allowlist` inclui *"script execution via heredoc"*, *"shell command via -c/-lc flag"* e *"script execution via -e/-c flag"*. Um pipeline escrito como heredoc **pede aprovação a cada passo, com 60 s de janela** — inviável para o Álvaro no celular. **Solução de projeto:** gravar os scripts como **arquivo** (`scripts/*.sh`, `scripts/*.py`) via tool `file` e executar o arquivo; e, para o trecho pesado, usar `delegation` — subagente tem `subagent_auto_approve: true`.
4. **STT do chat é o modelo `base`** (`stt.provider: local`). Nota de voz longa, técnica ou com nome próprio transcreve mal. Para pedido falado importante: **repetir o entendimento em uma linha antes de gastar**.
5. **Áudio vira texto antes de chegar ao agente.** Para usar a nota de voz como **referência de timbre**, é preciso ler o `.ogg` em `~/.hermes/audio_cache/` pelo `terminal` — o texto transcrito não serve.
6. **Cron roda sem o contexto do chat** e com `approvals.cron_mode: deny`. Job agendado precisa ser autossuficiente e não pode depender de `clarify`.
7. **Debounce de 5 s** junta mensagens em rajada numa chamada só — não responder duas vezes à mesma ordem.
8. **Chunking em 4.096 caracteres.** Resumo longo vira várias mensagens picotadas. Manter ≤8 linhas e mandar o `.md` como documento.
9. **Limite de anexo.** Vídeo confortável até ~16 MB; acima disso, link. `[[as_document]]` força envio como documento — útil para não perder qualidade na recompressão do WhatsApp.
10. **`vision_analyze` devolve texto, não pixels**, porque o modelo de chat é texto-only. Uma pergunta nova sobre o mesmo frame = chamada nova. Pedir tudo num prompt só.
11. **`allowed_chats`** está restrito ao número do Álvaro — nenhum outro chat aciona a skill (bom para custo, atenção ao testar de outro número).
12. **`hermes postinstall`** já instala `ffmpeg`, `node`, `ripgrep` e o browser — o `doctor` da skill deve checar antes de sair instalando.
13. **`delegation`:** `max_concurrent_children: 3`, `max_spawn_depth: 2`, modelos permitidos `deepseek-v4-pro`/`v4-flash`. Paralelismo real é 3, não N.
14. **Timeouts do gateway:** `gateway_timeout: 3600 s`, aviso em `1200 s`, `max_turns: 150`. Pipeline longo **tem que ser processo em background**, não sequência de tool calls.

---

## 6. ✅ Critérios de validação — o gate da Fase 1

**Todos precisam passar, testados pelo Álvaro no WhatsApp, antes de a Fase 2 começar.**

### Analisar
- [ ] Link de Reel mandado no WhatsApp → resumo no chat + `ANALISE.md` anexado, sem intervenção no terminal
- [ ] Link do YouTube (RM RAPS) → análise com cortes/min e BPM
- [ ] Vídeo mandado **como arquivo** → analisado sem baixar nada
- [ ] Reel do Instagram **com login** resolvido pela tool `browser`
- [ ] Toda afirmação de estilo no relatório tem `[mm:ss]` ou número
- [ ] Análise visual entregue pela tool `vision` do próprio Hermes

### Criar
- [ ] "faz um reel sobre X" → roteiro no chat → aprovação → `final_9x16.mp4` tocando dentro do WhatsApp
- [ ] Versão 16:9 do mesmo vídeo, reenquadrada
- [ ] Legendas dentro da safe area, confirmado pela autoverificação com `vision`
- [ ] Áudio a −14 LUFS
- [ ] O Hermes fez **no máximo 3 perguntas** no processo
- [ ] Pedido por **nota de voz** funcionou igual ao pedido por texto

### Dublar
- [ ] Reel pt→en entregue com desvio de sincronia **≤150 ms** (relatado no chat)
- [ ] Trilha original preservada (Demucs), narração nova por cima
- [ ] Legendas no idioma novo, geradas do áudio dublado real
- [ ] Trocadilho intraduzível virou **pergunta**, não invenção

### Protocolo (o que faz ser "pelo WhatsApp")
- [ ] Aceite em segundos em todos os fluxos
- [ ] Progresso chegou durante um job de +5 min, sem o Álvaro perguntar
- [ ] `clarify` renderizou lista numerada e a resposta "2" funcionou
- [ ] Timeout de 30 min sem resposta → estado salvo e "continua" retomou
- [ ] Nenhum passo pediu aprovação de comando no meio do pipeline (gotcha nº 3 resolvido)
- [ ] Print mandado no chat foi usado como referência visual
- [ ] Arquivo acima de 16 MB entregue por link, sem erro

**Assinatura do gate:** quando o Álvaro disser *"tá validado"* depois de rodar os três eixos pelo celular, a **Fase 2** é liberada. Antes disso, os outros quatro planos não começam.

---

## 7. Decisões em aberto (do Hermes, para o Hermes)

> Todas decididas pelo Álvaro em 2026-08-09 (via WhatsApp). Itens de configuração pendentes marcados com 🔧.

1. **Credencial de imagem** ✅ **DECIDIDO (2026-08-09)**: **geração própria + pesquisa de imagens + edição de estilo** (o fluxo que o Claude desenhou nos planos desta pasta). **Grok (criação de imagens) via API do Cursor** como opção quando necessário 🔧 (precisa configurar a credencial/endpoint do Cursor no Hermes). Modo A = material próprio + busca de imagens + zoompan; upgrade opcional = Grok image gen.
2. **`video_gen` no WhatsApp** ✅ **DECIDIDO**: **`image_gen` + `zoompan` como padrão** (custo zero, resolve ~80% do Modo A). `video_gen` continua só no toolset `cli`.
3. **Onde roda o job pesado** ✅ **DECIDIDO**: **local no acer como padrão**; o plano deve deixar **preparado para o PC Windows da IMAP** (pcque001imap, Tailscale) ser usado quando estiver ligado — **é o de melhor processamento; quando disponível, a skill prioriza executar lá** (SSH, mesmo padrão do server-desktop). 🔧 (definir host/credenciais do Windows no plano de execução).
4. **Modelo por etapa** ✅ — `deepseek-v4-flash` no operacional; `v4-pro` na síntese da fórmula e na tradução com restrição (recomendação do plano mantida).
5. **Fallback de visão** ✅ **DECIDIDO (2026-08-09)**: se a `GROQ_API_KEY` falhar, usar **a API do Cursor com Grok 4.5** (visão) 🔧 (configurar endpoint/chave do Cursor).
6. **Voz premium** ✅ **DECIDIDO (2026-08-09)**: **só grátis** — vozes bonitas que combinam com o estilo dos exemplos (RM RAPS/reels), usando **edge TTS** com seleção de vozes + opções locais (ex.: Piper) se necessário. **Sem ElevenLabs/API paga.**
