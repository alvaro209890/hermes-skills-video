# Plano — Skills de vídeo no **Codex**

**Princípio:** 🔒 **autonomia total.** O Codex executa o pipeline inteiro — baixar, transcrever, extrair e **ver** frames, analisar, roteirizar, gerar cenas, narrar, editar, exportar 9:16 e 16:9, e dublar — **sozinho**. Ele constrói as ferramentas **para si mesmo**, não para outros agentes. **Zero roteamento para outro agente.**
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
> ⚠️ **Tentação a evitar:** "o Codex constrói a CLI primeiro, e o Hermes usa". **Não.** Isso reintroduz dependência entre agentes e adia a única entrega que importa agora — o Hermes funcionando no WhatsApp. O Hermes constrói o que precisa, sozinho, com `terminal`.
>
> **Enquanto isso, o que pode ser feito aqui sem violar o gate:** nada de implementação. Este documento fica como especificação congelada.
>
> **Ao desbloquear, checklist de entrada:**
> - [ ] Gate do Hermes assinado pelo Álvaro
> - [ ] `ANALISE.md` e `videospec.json` reais, produzidos pelo Hermes, disponíveis como referência de formato
> - [ ] Gotchas do ambiente já registrados (README §3.4 e §4)
> - [ ] Decisão de credencial de imagem já tomada (Hermes §7, item 1)
> - [ ] Política de rede do sandbox resolvida (ver §4 deste plano)

---

## 0. O que o Codex tem para fechar o pipeline sozinho

| Necessidade do pipeline | Recurso próprio | Observação |
|---|---|---|
| **Ver keyframes** | **`codex -i frame.jpg`** — anexa imagem ao prompt (também em `codex exec`) | verificado: `-i, --image <FILE>...` |
| **Rodar yt-dlp, ffmpeg, whisper, Demucs** | execução de shell | ⚠️ atenção à rede do sandbox — §4 |
| **Instagram com login** | `yt-dlp --cookies-from-browser chrome` | exige execução fora do sandbox restrito |
| **Narração (TTS)** | `edge-tts` via shell | |
| **Gerar imagem/vídeo de cena** | API (fal.ai / Replicate) via shell | |
| **Paralelizar** | `codex exec` em loop, `tmux`, `xargs -P` | |
| **Construir e manter as ferramentas** | `src/vs/` do próprio projeto + `pytest` | é a força deste ambiente |
| **Instruções persistentes** | `AGENTS.md` + `~/.codex/config.toml` | `gpt-5.6-sol`, reasoning `high` |

**Vantagem própria (não exclusividade):** é o ambiente mais adequado a trabalho **algorítmico e reprodutível**. `model_reasoning_effort = "high"` e `plan_mode_reasoning_effort = "high"` já estão no `~/.codex/config.toml`; o sandbox e a política de aprovação tornam seguro mexer em arquivos grandes e chamar APIs pagas. Construir um pipeline de mídia é exatamente isso: muitos casos de borda, pouco improviso.

**Escolha o Codex quando** quiser o pipeline **testado**, com casos de borda cobertos e resultado reprodutível — em especial para a dublagem, que é o subsistema mais matemático do conjunto.

---

## 1. O que criar

```
~/Documentos/Video_Studio/codex/     # projeto próprio deste agente
├── AGENTS.md                        # regras invioláveis
├── bin/vs                           # CLI própria (uso deste agente)
├── src/vs/
│   ├── doctor.py  fetch.py  transcribe.py  scenes.py  keyframes.py  analyze.py
│   ├── tts.py     subs.py   render.py   check.py
│   ├── dub/  separate · translate · fit · mix · qa
│   └── spec.py                      # validação do videospec.json
├── tests/
│   ├── fixtures/                    # clipes de 5s, não vídeos de 4 min
│   └── test_*.py
└── docs/
    ├── CONTRATO.md                  # o videospec.json documentado
    ├── PLATAFORMAS.md               # limites de Reels/Shorts/TikTok/YouTube
    └── GOTCHAS.md                   # bloqueios conhecidos
```

> A CLI `vs` aqui é **deste agente, para este agente**. Se outro ambiente quiser algo parecido, escreve o seu. O que é comum entre os cinco é apenas o **formato de arquivo** (README §5), como `.srt` — não um binário compartilhado.

---

# SKILL 1 — `video-analise`

## 1.1 Objetivo

Analisar um vídeo ponta a ponta, com comandos **determinísticos, testados e idempotentes**, produzindo `ANALISE.md` com `[mm:ss]` — incluindo o eixo visual, lido pelo próprio agente via `-i`.

## 1.2 Quando usar (gatilhos)

- "analisa esse vídeo / esse reel"
- "extrai a estrutura e o ritmo desse edit"
- "o pipeline quebrou em <caso>"
- "a detecção de cena está contando errado"
- "adiciona suporte a <plataforma>"
- "escreve os testes do pipeline"

## 1.3 Fluxo passo a passo

**0. `vs doctor` — sempre primeiro.** Versões de `yt-dlp` e `ffmpeg`, presença de `faster-whisper`/`Demucs`/`PySceneDetect`/`rubberband`, VAAPI, disco, chaves de API, **e o acesso de rede do sandbox** (§4). Saída legível por humano **e** em JSON. Precedente da casa: o `imap doctor` evita prometer o que não sai.

**1. `vs fetch`** — resolve plataforma, aplica cookies quando preciso, grava `fonte.mp4` + `fonte.info.json` normalizado.
Casos de borda a tratar desde o início — todos observados no planejamento:
- `yt-dlp` do apt está **quebrado** para YouTube (`Requested format is not available`) → o `doctor` **recusa** versão antiga;
- URL do Instagram vem com `?igsh=…` → normalizar antes de derivar o slug;
- sem cookies no Instagram → mensagem clara com a ação sugerida, não stack trace;
- vídeo já baixado → não rebaixar (idempotência).

**2. `vs transcribe`** — `faster-whisper` + alinhamento por palavra, sobre `vocals.wav` quando há música (Whisper erra letra com beat alto). Modelo por parâmetro, padrão sensato para 11 GB de RAM.
**Decisão verificada:** **não** usar a legenda do YouTube — `timedtext` devolve 0 byte mesmo listando a trilha `pt/asr`.

**3. `vs scenes`** — `PySceneDetect` + métricas: cortes/min, média e mediana de plano, desvio, keyframes. Modo B: BPM e **% de cortes na batida** (±80 ms).
Caso de borda conhecido: edit com flash constante gera falso positivo em `detect-adaptive` → expor o limiar e registrar a taxa de descarte.

**4. `vs keyframes`** — extrai ~15 frames representativos, nomeados por timestamp (`00m03s.jpg`), prontos para anexar.

**5. 👁️ Leitura visual — aqui mesmo.** O agente roda `codex -i refs/<slug>/keyframes/*.jpg` (ou anexa no turno atual) com um prompt fixo pedindo paleta, enquadramento, tipo de material, **estilo de legenda** (fonte, peso, contorno, posição, karaokê) e efeitos. Em lotes de 6 a 10.

**6. `vs analyze`** — consolida tudo em `ANALISE.md`: o comando **calcula todos os números** e deixa marcado `<!-- VISUAL -->` onde entra a leitura de frames, que o próprio agente preenche no mesmo turno.

**7. Testes** com fixtures de 5 s — nunca com o vídeo de 4 min. Suíte que roda em menos de um minuto é suíte que se roda de fato.

## 1.4 Ferramentas necessárias

`python 3.11` + `uv` · `yt-dlp` (novo) · `ffmpeg`/`ffprobe` · `faster-whisper` · `WhisperX` · `Demucs` · `PySceneDetect` · `librosa` · `pytest` · `codex -i` para visão.

## 1.5 Como o Codex executaria

- **`AGENTS.md`** com as regras invioláveis: todo comando idempotente; toda falha com mensagem acionável; nada de caminho absoluto embutido; mudança no `videospec.json` atualiza `docs/CONTRATO.md` no mesmo commit.
- **`trust_level = "trusted"`** para o diretório do projeto no `~/.codex/config.toml` (padrão que o Álvaro já usa nos outros projetos).
- **Plan mode com reasoning alto** antes de escrever — o pipeline tem muitos casos de borda e refazer sai caro.
- **`codex exec`** para rodar a suíte e para lotes.
- **Fixtures locais** durante o desenvolvimento, o que contorna o bloqueio de rede do sandbox na maior parte do tempo.

## 1.6 Limitações

- **Rede bloqueada no sandbox** (§4) — atrapalha justamente `fetch`, download de modelo e TTS.
- **11 GB de RAM** limitam teste com modelos grandes.
- **Plataformas mudam sem aviso** — manutenção é permanente, não "pronto uma vez".
- **Julgamento estético** continua humano; o pipeline entrega números e descrições.

## 1.7 Próximos passos

1. Escrever `docs/CONTRATO.md` **antes** de qualquer código.
2. Implementar `vs doctor` primeiro — destrava o diagnóstico de todo o resto.
3. Montar fixtures: 1 clipe 9:16 com legenda queimada, 1 clipe 16:9 com música, 1 áudio bilíngue.

---

# SKILL 2 — `video-criacao`

## 2.1 Objetivo

Do briefing ao arquivo final, com **verificação automática de conformidade** — a característica que distingue este ambiente: nada é entregue sem passar na checagem.

## 2.2 Quando usar (gatilhos)

- "faz um reel sobre X"
- "o render está saindo com a legenda cortada"
- "adiciona a transição <x>"
- "acelera o render"
- "valida se o arquivo está dentro da spec do Reels"
- "o áudio está baixo demais"

## 2.3 Fluxo passo a passo

1. **Roteiro** pela fórmula do Modo A (README §3.2), a ~**2,7 palavras/segundo**.
2. **`vs spec validate`** — rejeitar spec inválido **antes** de gastar minutos de render: soma das cenas × duração alvo, assets existentes, voz suportada, teto de custo.
3. **Assets:** imagem por API + `zoompan`; vídeo generativo só onde o movimento é o ponto; clipe de anime como último recurso (README §9.1).
4. **`vs tts`** — um `.wav` por cena, **cache por hash** (texto+voz+ritmo), devolvendo a **duração real** ao spec: o TTS quase nunca entrega o tempo previsto, e todo o timing depende disso.
5. **`vs subs`** — transcrição da **narração sintetizada** → `.ass` karaokê. Regras embutidas: safe area (x 100–860, y 300–1450 em 1080×1920), máximo de palavras por cartela, contorno e sombra do preset.
6. **`vs render`** — cenas → transições → legendas → mix com ducking → `loudnorm` 2 passes (−14 LUFS, pico −1 dBTP) → export.
   Otimizações que valem: **VAAPI** (`h264_vaapi`, confirmado disponível); `concat` sem re-encode quando não há transição; renderizar 9:16 e reenquadrar para 16:9 num segundo passe.
7. **`vs check`** — via `ffprobe`: resolução e proporção, duração dentro do limite da plataforma, LUFS na faixa, faixa de áudio presente e não silenciosa, `faststart`, tamanho. **Falhou = não entrega.**
8. **👁️ Prova visual** — anexar 4 keyframes do render com `-i` e confirmar: legenda cortada? dentro da safe area? legível sobre o fundo?

### Identidade visual, aqui

O preset (`jjk-dark`) mora em `docs/` e é aplicado por `.ass` + filtros do `ffmpeg`. Se um projeto pedir composição mais elaborada, **este agente instala Remotion por conta própria** e renderiza com `--props videospec.json` — ferramenta do SO, não serviço de outro agente.

## 2.4 Ferramentas

`ffmpeg` (`concat`, `xfade`, `zoompan`, `ass`, `loudnorm`, `sidechaincompress`, `h264_vaapi`) · `ffprobe` · `edge-tts` · `libass` · `faster-whisper` · API de imagem · Remotion (opcional).

## 2.5 Como o Codex executaria

Construir com **casos de teste de conformidade** desde o começo: cada regra de plataforma vira um teste em `tests/`. É a disciplina que este ambiente sustenta melhor — transformar uma lista de requisitos chatos em verificação automática.

## 2.6 Limitações

- **`xfade` re-encoda tudo** — caro em vídeo longo; VAAPI ajuda, com alguma perda frente a `libx264` CRF baixo. Expor a escolha.
- **`sidechaincompress` é sensível a parâmetro** — começar com ganho fixo interpolado, que é previsível.
- **Fonte precisa estar instalada**, senão `libass` cai em fallback silencioso e ninguém percebe até ver o arquivo.
- **Reenquadrar 9:16 → 16:9** é imperfeito → sinalizar baixa confiança em vez de entregar recorte ruim como bom.
- **TTS não faz entonação de rap** — o Modo B segue o pipeline "guia de voz humana + IA" do RM RAPS.

## 2.7 Próximos passos

1. Escrever `docs/PLATAFORMAS.md` com a lista de conformidade por plataforma.
2. Medir `libx264` × `h264_vaapi` neste hardware: tempo e qualidade.
3. Implementar o cache de TTS — a economia mais fácil do pipeline.

---

# SKILL 3 — `video-dublagem`

## 3.1 Objetivo

`vs dub <slug> --para <idioma>`: trocar a narração de idioma preservando **sincronia**, **trilha original** e **intenção**, com QA numérico verificável.

## 3.2 Quando usar (gatilhos)

- "dubla esse vídeo pra inglês/espanhol"
- "a dublagem está dessincronizada"
- "a voz dublada está acelerada demais"
- "sumiu a música do vídeo dublado"
- "adiciona suporte ao idioma <x>"

## 3.3 Fluxo passo a passo — o algoritmo

**1. Separar** (`Demucs htdemucs`) → `vocals.wav` + `music.wav`.
A `music.wav` é **preservada intacta** — é o que faz a versão dublada continuar soando como o original.

**2. Segmentar por unidade de fala.** Cortar por pausa real (>200 ms de silêncio em `vocals.wav`), **não** por frase gramatical. Cada segmento carrega `inicio`, `fim`, `duracao_alvo`, `texto`.

**3. Traduzir com restrição de duração — o próprio Codex traduz.**
A camada que mais decide o resultado. Cada segmento recebe o orçamento de caracteres estimado pela taxa de fala do idioma alvo:

```
alvo_caracteres ≈ duracao_alvo_s × taxa_do_idioma
```

Taxas a calibrar empiricamente (pt-BR ≈ 14–16 caracteres/s narrado; inglês costuma render ~15–30 % **menos** texto para a mesma ideia). Pedir **3 variantes** por segmento — curta, média e longa — e escolher na etapa de encaixe. Muito mais barato que reprocessar quando estourar.

**4. Sintetizar** cada segmento e **medir a duração real**.

**5. Encaixe temporal — em cascata, nesta ordem:**

| Ordem | Ação | Limite |
|---|---|---|
| 1 | escolher a variante que melhor encaixa | grátis, sempre tentar primeiro |
| 2 | absorver a diferença no **silêncio adjacente** | até o silêncio disponível |
| 3 | `rubberband` preservando pitch | **±10 %** — além disso é audível |
| 4 | pedir nova tradução mais curta | se ainda estourar |
| 5 | marcar para revisão humana | quando nada resolve |

**A ordem importa.** Ir direto ao *time-stretch* é o que produz aquela dublagem apressada e robótica. Reescrever o texto é quase sempre superior a esticar o áudio.

**6. Remixar:** narração + `music.wav` com ducking → `loudnorm`.

**7. QA numérico** (`vs dub qa`): desvio de início e fim por segmento, média, p95, pior caso. **Meta: ≤150 ms.** Saída em JSON com os 5 piores por timestamp — o revisor assiste 5 trechos, não o vídeo inteiro.

**8. Legendas** no idioma novo, geradas do áudio dublado real (não da tradução prevista).

## 3.4 Ferramentas

`Demucs` · `WhisperX` (alinhamento forçado — indispensável aqui) · **o próprio modelo** para tradução com restrição · `edge-tts` multi-idioma **ou ElevenLabs Dubbing** · `rubberband-cli` · `ffmpeg`.

⚠️ **Licenças a registrar no spec:** XTTS-v2 é **CPML — proíbe uso comercial**. Voz clonada de pessoa real exige autorização. O `vs` grava motor e licença usados em cada saída.

## 3.5 Como o Codex executaria

É o trabalho em que o reasoning alto se paga: um algoritmo em cascata com muitos casos de borda (segmento sem silêncio adjacente, fala sobreposta, trocadilho intraduzível, idioma sem voz decente).

**Decisão a tomar cedo, com honestidade:** avaliar **ElevenLabs Dubbing** contra o pipeline próprio antes de construir tudo. Se a API entregar sincronia melhor por custo aceitável, `vs dub` vira um **wrapper** com o pipeline local como alternativa gratuita — não faz sentido construir por orgulho o que já existe pronto e melhor.

## 3.6 Limitações

- **Sem lip-sync.** Wav2Lip/LatentSync ficam fora por qualidade e licença. Irrelevante para narração em off e anime edit; **bloqueante** para talking head — a skill deve avisar ao ser acionada nesse caso.
- **Trocadilho não sobrevive.** "Técnica Amaldiçoada: *Você Que Sabe*" não tem equivalente direto em inglês → **sinalizar**, não inventar.
- **Demucs em CPU: ~5–10× tempo real.** Reel de 30 s tranquilo; clipe de 4 min, rodar em background e avisar o tempo.
- **Fala sobreposta** quebra a segmentação → detectar e marcar.
- **Prosódia:** TTS não reproduz ironia, e o tom das referências **é** irônico.
- **Modo B é outro problema:** dublar rap com métrica e rima é reescrita criativa, não tradução — fora do escopo de `vs dub`.

## 3.7 Próximos passos

1. **Comparar ElevenLabs Dubbing × pipeline próprio** num Reel de 30 s pt→en — essa medição decide a arquitetura do subsistema.
2. Calibrar empiricamente as taxas de caracteres/segundo por idioma.
3. Implementar o QA numérico **antes** do encaixe: precisa existir o termômetro antes de tentar melhorar a temperatura.

---

## 4. Configuração do Codex para este projeto ⚠️

O ponto que mais custa tempo se for descoberto tarde:

| Item | Situação | Ação |
|---|---|---|
| **Rede no sandbox** | `workspace-write` **bloqueia rede por padrão** → `yt-dlp`, download de modelo Whisper, `edge-tts` e APIs falham | habilitar acesso de rede para este projeto, ou desenvolver com fixtures locais e rodar `fetch` com a política adequada |
| `trust_level` | outros projetos do Álvaro já são `trusted` | acrescentar o diretório do projeto |
| Modelo | `gpt-5.6-sol`, reasoning `high` | manter — é trabalho algorítmico |
| **Visão** | `codex -i <arquivo>` aceita imagens | usar para keyframes; sem dependência externa |
| Chaves de API | ElevenLabs, fal.ai/Replicate | fora do repositório; padrão `secrets.local.json`, como nos outros projetos |
| Arquivos grandes | vídeos no workspace | `.gitignore` para `refs/`, `render/`, `*.mp4` — **git com vídeo é armadilha** |

## 5. Autonomia — nada sai daqui

| Etapa | Como o Codex resolve **sozinho** |
|---|---|
| Ver keyframes | `codex -i frame.jpg`, em lotes |
| Instagram com login | `yt-dlp --cookies-from-browser chrome`, com a política de sandbox certa |
| Paralelismo | `codex exec` em loop, `tmux`, `xargs -P` |
| Narração | `edge-tts` via shell |
| Identidade visual | preset em `docs/` aplicado por `.ass`; Remotion instalado pelo próprio projeto se precisar |
| Tradução da dublagem | o próprio modelo |
| Verificar o resultado | `vs check` (`ffprobe`) + leitura de keyframes por `-i` |
| Ferramenta faltando ou quebrada | escreve/corrige em `src/vs/` e cobre com teste |

O formato comum (README §5) permite **abrir** artefatos vindos de outro ambiente, mas nada aqui **depende** disso.

**Sobre o contrato:** `docs/CONTRATO.md` documenta o `videospec.json` **desta implementação**. Campos novos são bem-vindos; campos desconhecidos são ignorados em vez de causar erro — formato tolerante é o que permite cinco implementações independentes conviverem sem nenhuma depender das outras.
