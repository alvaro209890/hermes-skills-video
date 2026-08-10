# Plano — Skills de vídeo no **OpenCode**

**Princípio:** 🔒 **autonomia total.** O OpenCode executa o pipeline inteiro — baixar, transcrever, extrair e **ver** frames, analisar, roteirizar, gerar cenas, narrar, editar, exportar 9:16 e 16:9, e dublar — **sozinho**, headless. **Zero roteamento para outro agente.** Paralelismo vem dos **subagentes internos** dele (`.opencode/agent/`).
**Status:** planejamento. Nada implementado.
📖 Contexto comum: [`README.md`](README.md).

---

## 🚦 ORDEM DE EXECUÇÃO / GATE

> ## ⛔ **FASE 2 — NÃO COMEÇAR AINDA.**
>
> | | |
> |---|---|
> | **Fase** | **2 — bloqueada** |
> | **Bloqueado por** | [`PLANO_HERMES.md`](PLANO_HERMES.md) — os 3 eixos validados pelo Álvaro **no WhatsApp** |
> | **Libera quando** | todos os itens da §6 do plano do Hermes estiverem marcados e o Álvaro disser "tá validado" |
>
> A skill de vídeo do **Hermes** é desenvolvida, testada e validada **100% primeiro**. Só depois este plano sai do papel. Não há motivo para dividir esforço: o pipeline é o mesmo, e os erros descobertos no Hermes (formato de `videospec.json`, prompt de visão, cascata de sincronia, presets de identidade) chegam aqui já resolvidos.
>
> **Enquanto isso, o que pode ser feito aqui sem violar o gate:** nada de implementação. Este documento fica como especificação congelada.
>
> **Ao desbloquear, checklist de entrada:**
> - [ ] Gate do Hermes assinado pelo Álvaro
> - [ ] `ANALISE.md` e `videospec.json` reais, produzidos pelo Hermes, disponíveis como referência de formato
> - [ ] Gotchas do ambiente já registrados (README §3.4 e §4)
> - [ ] Decisão de credencial de imagem já tomada (Hermes §7, item 1)
> - [ ] Provider com visão escolhido e declarado no `opencode.jsonc` (ver §0 deste plano)

---

## 0. O que o OpenCode tem para fechar o pipeline sozinho

| Necessidade do pipeline | Recurso próprio | Observação |
|---|---|---|
| **Rodar yt-dlp, ffmpeg, whisper, Demucs** | ferramenta de bash | mesmo SO |
| **Ver keyframes** | **provider com visão configurado no `opencode.jsonc`** | multi-provider: Groq (`llama-4-scout`), Anthropic, Google — `opencode models` lista o que está disponível |
| **Instagram com login** | `--cookies-from-browser chrome` (local) ou cookies exportados (servidor) | §1.7 |
| **Narração (TTS)** | `edge-tts` via bash | grátis, pt-BR |
| **Gerar imagem/vídeo de cena** | API (fal.ai / Replicate) via bash | |
| **Paralelizar** | **subagentes internos** (`.opencode/agent/*.md`) + `opencode run` em loop | um subagente por vídeo/idioma/lote de frames |
| **Automatizar** | `.opencode/command/*.md`, plugins TS, `opencode serve`, MCP | `~/.config/opencode/` já tem `commands/` e plugins Node |
| **Rodar longe do notebook** | `server-desktop` via Tailscale/SSH | continua sendo *o OpenCode* executando |

**Vantagem própria (não exclusividade):** headless de verdade (`opencode run "<prompt>"` executa e sai), multi-provider por config (modelo barato onde o trabalho pesado é `ffmpeg` e Whisper, não o LLM) e uma casa natural no `server-desktop`, onde Demucs e Whisper não competem com o notebook.

**Escolha o OpenCode quando** forem muitos vídeos, ou quando o trabalho puder rodar de madrugada. Mas ele entrega **um** vídeo completo tão bem quanto os outros quatro.

---

## 1. O que criar

```
~/Documentos/Video_Studio/.opencode/
├── agent/
│   ├── video-completo.md      # primary: pipeline ponta a ponta de 1 vídeo
│   ├── video-analista.md      # subagent: 1 vídeo → ANALISE.md
│   ├── video-visual.md        # subagent com PROVIDER DE VISÃO: lê lotes de keyframes
│   ├── video-dublador.md      # subagent: 1 idioma
│   └── video-lote.md          # primary: orquestra a fila
├── command/
│   ├── analisar.md            # /analisar <url>
│   ├── criar-reel.md          # /criar-reel <tema>
│   ├── dublar.md              # /dublar <slug> <idiomas>
│   ├── analisar-lote.md       # /analisar-lote <arquivo-de-urls>
│   ├── render-variacoes.md    # /render-variacoes <slug> <n>
│   └── relatorio-nicho.md     # /relatorio-nicho <slug-do-lote>
├── plugin/
│   └── video-hooks.ts         # notificações e telemetria de job
└── scripts/                   # pipeline próprio (bash/python)
    ├── doctor.sh  fetch.sh  transcribe.sh  scenes.sh  keyframes.sh
    ├── tts.sh     render.sh   dub/
```

Config em `opencode.jsonc`: **modelo barato como padrão**, **um modelo com visão declarado para o agente `video-visual`**, `bash` permitido dentro de `~/Documentos/Video_Studio`, `webfetch` habilitado (necessário para `yt-dlp`).

---

# SKILL 1 — `video-analise`

## 1.1 Objetivo

Analisar **1 vídeo** ponta a ponta (incluindo o eixo visual) e, quando for o caso, **N vídeos** — produzindo, além dos relatórios individuais, o entregável que só existe em escala: um **relatório comparativo de nicho**.

## 1.2 Quando usar (gatilhos)

**Um vídeo:** "/analisar <url>", "analisa esse reel", "extrai a estrutura desse vídeo".
**Lote:** "analisa os últimos N vídeos desse perfil/canal", "compara esses 15 reels", "qual o padrão de hook do nicho", "processa essa lista de links", "roda a análise de madrugada".

## 1.3 Fluxo passo a passo — um vídeo

**0. `doctor`** (`scripts/doctor.sh`): `yt-dlp` **novo** (a do apt está quebrada — README §3.4), `ffmpeg`, `faster-whisper`, `Demucs`, `PySceneDetect`, disco, **e um teste do provider de visão** (`opencode models` + uma chamada curta).

**1. Baixar** → `yt-dlp` (cookies quando necessário).
**2. Áudio e faixas** → `ffmpeg` + `Demucs` (`vocals.wav`, `music.wav`).
**3. Transcrever** → `faster-whisper` + alinhamento por palavra, sobre `vocals.wav` quando há música.
⚠️ **Não usar a legenda do YouTube:** `timedtext` devolve 0 byte.
**4. Cortes e ritmo** → `PySceneDetect`: cortes/min, média, mediana, desvio; Modo B: BPM e **% de cortes na batida**.
**5. Keyframes** → `ffmpeg`, ~15 representativos.
**6. 👁️ Ver os frames — subagente `video-visual`**, que roda **com um provider de visão** declarado no `opencode.jsonc`. Recebe lotes de frames e devolve paleta, enquadramento, tipo de material, estilo de legenda e efeitos. O subagente é **interno ao OpenCode**; a análise visual acontece aqui.
**7. Áudio** → `loudnorm`: LUFS, ducking, tipo de voz.
**8. `ANALISE.md`** pela rubrica comum, com `[mm:ss]` e números.

## 1.4 Fluxo passo a passo — lote (a força deste ambiente)

1. **Montar a fila.**
   ```bash
   # ilustrativo
   yt-dlp --flat-playlist --print "%(url)s" "https://www.youtube.com/@CANAL/videos" | head -30 > fila.txt
   ```
2. **Fase paralela pesada (sem LLM):** `fetch` → `transcribe` → `scenes` por item. Paralelismo governado por **RAM**, não por CPU (Whisper `medium` int8 ≈ 2–3 GB) → **2 a 3 jobs simultâneos**, com `nice` para não competir com outros serviços do servidor.
3. **Fase visual:** o subagente `video-visual` processa **uma amostra** de frames por vídeo (ver §1.7 sobre custo).
4. **Fase de síntese:** um subagente `video-analista` por vídeo redige o relatório a partir dos números já calculados — o LLM **não recalcula nada**.
5. **Tabela consolidada** (`lote.csv`): duração, cortes/min, mediana de plano, palavras/min, LUFS, tem trilha, tem narração, palavras do hook, posição do CTA, views, likes, comentários.
6. **Relatório comparativo** — o entregável real: padrões de hook agrupados, faixa de ritmo dos que performam, CTAs mais usados, e **outliers** (o vídeo que foge do padrão e mesmo assim vai bem costuma ser o achado mais útil).

## 1.5 Ferramentas necessárias

`yt-dlp` (novo) · `ffmpeg` · `faster-whisper` · `WhisperX` · `Demucs` · `PySceneDetect` · `librosa` · provider de visão no `opencode.jsonc` · `opencode run --agent` · `xargs -P`/`parallel` · `nice`/`ionice` · `cron` · CSV/sqlite para estado da fila · SSH/Tailscale para o `server-desktop`.

## 1.6 Como o OpenCode executaria

- **Um primário que orquestra, subagentes que executam** — 30 vídeos numa sessão só estouraria a janela; cada análise fica isolada.
- **Estado em disco, não em contexto:** a fila é um arquivo com status por item (`pendente`/`ok`/`erro`), então um job de madrugada retoma depois de uma queda.
- **Modelo por etapa:** barato para redigir; com visão para os frames; um pouco melhor só para o comparativo final.
- **Disparo remoto:**
  ```bash
  # ilustrativo
  ssh server-desktop 'cd ~/Documentos/Video_Studio && opencode run --agent video-lote "processa fila.txt"'
  ```
- **Falha não pára o lote:** item com erro é marcado, o lote segue, e o relatório final lista o que não entrou.

## 1.7 Limitações

- **Visão custa em lote.** Ver 15 frames × 30 vídeos = 450 chamadas. Política recomendada: **amostra de 4–6 frames por vídeo** na varredura, e leitura completa só nos finalistas — **dentro do próprio OpenCode**, trocando o agente, não o agente-dono.
- **Instagram no servidor headless.** Sem sessão de navegador, o download falha. Caminhos próprios: rodar a etapa de download na máquina local (onde o Chrome está logado) e depois seguir no servidor; ou manter um arquivo de cookies exportado, com validade curta. **Realidade a aceitar:** lote funciona bem para YouTube/Shorts; Instagram é semi-manual.
- **Rate limit:** 30 downloads seguidos podem levar bloqueio → `--sleep-requests`.
- **Qualidade textual menor** com modelo barato → rubrica rígida, e a maior parte do conteúdo vindo de número medido, não de opinião do modelo.
- **Correlação não é causa.** O relatório diz "os que performaram têm X", nunca "faça X e vai performar" — o contraste 3,08 M × 14,7 k do RM RAPS, com pipeline idêntico, é a prova.
- **Disco:** 30 vídeos em 1080p passam de 10 GB → apagar `fonte.mp4` após extrair áudio e keyframes.

## 1.8 Próximos passos

1. Declarar no `opencode.jsonc` qual provider/modelo o agente `video-visual` usa, e testar com 3 frames.
2. Confirmar se o `server-desktop` tem GPU utilizável — muda o dimensionamento do lote inteiro.
3. Piloto com 10 vídeos do YouTube medindo tempo e custo por vídeo.

---

# SKILL 2 — `video-criacao`

## 2.1 Objetivo

Produzir vídeo completo — **um** por pedido, ou **N variações** quando o objetivo for testar.

## 2.2 Quando usar (gatilhos)

- "/criar-reel <tema>"
- "faz um reel sobre X no estilo do <slug>"
- "faz 5 versões desse reel com hooks diferentes"
- "renderiza esses 8 videospecs"
- "gera a versão 16:9 de tudo que está na pasta"
- pauta programada por `cron`

## 2.3 Fluxo passo a passo

1. **Roteiro** pela fórmula do Modo A (README §3.2), a ~**2,7 palavras/segundo**.
2. **`videospec.json`** a partir do preset de identidade (mantido em `references/` do próprio projeto).
3. **Assets:** imagem por API + `zoompan` (resolve ~80 % do Modo A); vídeo generativo só onde o movimento é o ponto; clipe de anime como último recurso (README §9.1).
4. **Narração** — `edge-tts` por cena, com a **duração real** devolvida ao spec.
5. **Legendas** transcrevendo a narração sintetizada → `.ass` karaokê na safe area.
6. **Edição/export** — `ffmpeg`: `concat` → transições → `ass` → mix com ducking → `loudnorm` −14 LUFS → **VAAPI** quando disponível. 9:16 + 16:9.
7. **Verificação automática** — `ffprobe`: resolução, proporção, duração, LUFS, faixa de áudio não silenciosa, `faststart`. Reprovado volta para a fila com o motivo.
8. **👁️ Prova visual** — o subagente `video-visual` lê 4 keyframes do render: legenda cortada? dentro da safe area? legível sobre o fundo?

**Em modo variações:** um spec-base + **um eixo por vez** (hook, voz, ritmo), **reaproveitando assets agressivamente** — 5 variações de hook compartilham as cenas 2 a 6; só o que muda é re-sintetizado e re-renderizado. É o que torna o lote barato. Entregar um **contato-folha** (keyframes de cada variação + tabela comparativa) para escolher sem abrir 5 arquivos.

## 2.4 Ferramentas

`edge-tts` · `ffmpeg` (+VAAPI) · `ffprobe` · API de imagem · `faster-whisper` · `montage`/`ffmpeg` para o contato-folha · `parallel` · subagente de visão.

## 2.5 Como o OpenCode executaria

Loop determinístico, LLM só onde há texto a criar. Render longo em `tmux`/`nohup` no servidor, resultado copiado de volta por `rsync`. Variações em paralelo por subagentes internos.

## 2.6 Limitações

- **API de imagem custa por variação** → reaproveitar assets é obrigatório.
- **Julgamento estético final é humano** — a prova visual pega erro objetivo, não gosto.
- **Fila longa de madrugada** pode esbarrar em rate limit → backoff.
- **Fonte precisa estar instalada** no servidor, senão `libass` cai em fallback silencioso.

## 2.7 Próximos passos

1. Definir o formato "spec-base + eixo de variação".
2. Escrever a lista de verificação automática de qualidade.
3. Piloto: 3 variações de hook do mesmo roteiro.

---

# SKILL 3 — `video-dublagem`

## 3.1 Objetivo

Dublar um vídeo para **1 ou N idiomas**, aproveitando que as etapas caras (separação e transcrição) são feitas uma única vez.

## 3.2 Quando usar (gatilhos)

- "/dublar <slug> en,es"
- "dubla pra inglês, espanhol e francês"
- "dubla esses 10 vídeos pro inglês"
- "roda a dublagem de madrugada"

## 3.3 Fluxo passo a passo

1. **Etapas compartilhadas, uma vez:** `Demucs` → `vocals.wav` + `music.wav`; transcrição com timestamp por palavra.
   *É aqui que o lote ganha:* Demucs é a etapa mais lenta do pipeline e roda **uma vez para todos os idiomas**.
2. **Por idioma, em paralelo** (subagente `video-dublador`): tradução com restrição de duração (3 variantes por segmento) → TTS → encaixe em cascata (variante → silêncio → `rubberband` ±10 % → nova tradução → marcar) → remix com a `music.wav` comum → legendas.
3. **QA por idioma:** desvio médio, p95, pior segmento. Reprovado (>150 ms) volta para nova tentativa de tradução mais curta.
4. **Entregar a tabela de QA** junto com os arquivos, para saber onde conferir sem assistir tudo.

## 3.4 Ferramentas

`Demucs` · `WhisperX` · LLM para tradução — **atenção: é a etapa que mais decide a qualidade final; vale um modelo melhor mesmo em lote** · `edge-tts` multi-idioma ou ElevenLabs · `rubberband` · `ffmpeg`.
⚠️ XTTS-v2 é CPML (não comercial); voz clonada de pessoa real exige autorização.

## 3.5 Como o OpenCode executaria

Um subagente interno por idioma, em paralelo, sobre os artefatos compartilhados. Estado em disco para retomada. 5 idiomas de um Reel de 30 s são poucos minutos depois do Demucs.

## 3.6 Limitações

- **Demucs em CPU é o gargalo** (~5–10× tempo real) → confirmar GPU no servidor.
- **Tradução em lote sem revisão** transforma trocadilho em literal → marcar segmentos suspeitos, nunca silenciar.
- **Idiomas sem voz boa em `edge-tts`** exigem provedor pago.
- **Sem lip-sync.**

## 3.7 Próximos passos

1. Medir o tempo do Demucs no `server-desktop` — define a escala possível.
2. Escolher os 3 idiomas iniciais (sugestão: en, es, e pt-BR como alvo para conteúdo importado).
3. Piloto: 1 vídeo → 3 idiomas, com tabela de QA.

---

## 4. Autonomia — nada sai daqui

| Etapa | Como o OpenCode resolve **sozinho** |
|---|---|
| Ver keyframes | subagente `video-visual` com provider de visão no `opencode.jsonc` |
| Instagram com login | download na máquina local com cookies do Chrome, ou cookies exportados |
| Paralelismo / lote | subagentes internos + `opencode run` + `parallel` |
| Rodar longe do notebook | `server-desktop` por SSH — continua sendo o OpenCode executando |
| Narração | `edge-tts` via bash |
| Identidade visual | preset próprio, aplicado por `.ass` + filtros do `ffmpeg` |
| Tradução da dublagem | modelo do próprio OpenCode (subir de tier nesta etapa) |
| Verificar o resultado | `ffprobe` + subagente de visão nos keyframes |
| Ferramenta faltando ou quebrada | edita `scripts/` e `.opencode/` na hora |

O formato comum (README §5) permite **abrir** artefatos vindos de outro ambiente — mas nada aqui **depende** disso; o pipeline cria a estrutura do zero.

**Nota honesta sobre a especialidade:** rodar o pipeline dezenas de vezes seguidas faz do lote o melhor descobridor de bugs do conjunto. Quando um bug aparecer, **o próprio OpenCode conserta** os seus scripts — e vale anotar o achado onde os outros ambientes possam ler, já que os mesmos casos de borda vão aparecer lá.
