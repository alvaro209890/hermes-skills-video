# Plano — Skills de vídeo no **Claude Code**

**Princípio:** 🔒 **autonomia total.** O Claude Code executa o pipeline inteiro — análise, criação e dublagem — **sozinho**, no terminal, com as ferramentas do próprio ambiente. **Zero roteamento para outro agente.** Paralelismo, quando preciso, sai de **subagentes internos** (`Explore`, `general-purpose`) e de jobs em background.
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

---

## 0. O que o Claude Code tem para fechar o pipeline sozinho

| Necessidade do pipeline | Recurso próprio | Observação |
|---|---|---|
| **Ver keyframe** | `Read` de `.jpg`/`.png` — **visão nativa** | descreve enquadramento, paleta, tipografia da legenda olhando |
| **Rodar yt-dlp, ffmpeg, whisper, TTS** | `Bash` | inclusive `run_in_background` para job longo |
| **Site com login (Instagram)** | skill **`chrome-agente`** (CDP, Chrome logado) | lê o DOM e faz `fetch` de dentro da página autenticada |
| **Paralelizar** | subagentes internos + `Bash` em background | vários comandos independentes num único bloco |
| **Escrever/consertar as próprias ferramentas** | `Write`/`Edit` em `~/.claude/skills/<skill>/scripts/` | cada skill carrega o que precisa |
| **Segunda opinião** | skill `deepseek-subagent` | ⚠️ **sem visão** — mandar texto, nunca keyframes |
| **Memória entre sessões** | memória de projeto | guardar presets e gotchas de plataforma |

**Vantagem própria (não exclusividade):** é o único que **enxerga nativamente**, sem intermediário nem chave de API — o keyframe entra direto no contexto. Isso torna a análise visual e a autorrevisão do render mais baratas e mais finas aqui do que em qualquer outro ambiente.

**Escolha o Claude Code quando** estiver no terminal e quiser olhar junto, iterando com atenção em um vídeo.

---

## 1. Skills a criar

```
~/.claude/skills/
├── video-analise/
│   ├── SKILL.md
│   ├── scripts/            # ferramentas próprias desta skill
│   └── references/
│       ├── rubrica-analise.md      # o que medir e como reportar
│       ├── estilos-referencia.md   # Modo A (@silv.mind) e Modo B (RM RAPS)
│       └── troubleshooting.md      # bloqueios de plataforma conhecidos
├── video-criacao/
│   ├── SKILL.md
│   ├── scripts/
│   └── references/
│       ├── formulas-roteiro.md · presets-identidade.md · specs-export.md
└── video-dublagem/
    ├── SKILL.md
    ├── scripts/
    └── references/sincronia.md
```

Cada skill é **autocontida**: traz seus próprios scripts auxiliares e seu próprio `doctor`. Nada é importado de outro agente.

---

# SKILL 1 — `video-analise`

## 1.1 Objetivo

Dado um link (YouTube / Reels / TikTok / Shorts) ou arquivo local, produzir um **`ANALISE.md` com referências de tempo `[mm:ss]`** que permita **replicar o estilo** — não apenas descrever o assunto. Cobre os 8 eixos: roteiro, estrutura, estilo visual, ritmo, transições, legendas, narração/dublagem e música.

## 1.2 Quando usar (gatilhos)

- "analisa esse vídeo / esse reel / esse short"
- "quero fazer um vídeo no estilo desse aqui"
- "por que esse vídeo bombou e o outro não"
- "extrai o roteiro / a estrutura desse vídeo"
- "qual o ritmo de edição desse edit"
- colar **qualquer URL** de youtube.com, youtu.be, instagram.com/reel, tiktok.com, youtube.com/shorts

## 1.3 Fluxo passo a passo

**0. `doctor` próprio (obrigatório).** Verificar `yt-dlp` **novo** (a do apt está quebrada — README §3.4), `ffmpeg`, `faster-whisper`, `Demucs`, `PySceneDetect`, disco. Faltou algo → **instalar na hora** (`uv tool install`) ou dizer o que falta antes de começar, nunca no meio.

**1. Aquisição.**
```bash
# ilustrativo
yt-dlp -f "bv*[height<=1080]+ba/b" --write-info-json -o "refs/<slug>/fonte.%(ext)s" "<url>"
# Instagram/TikTok: acrescentar --cookies-from-browser chrome
```
Falhou por login → **`chrome-agente`**: abre o Reel no Chrome já logado e captura o `.mp4` pela rede. Foi assim que os Reels de `@silv.mind` foram identificados no planejamento.

**2. Áudio e faixas.** `audio.wav` (16 kHz mono para transcrever, 48 kHz estéreo para medir); `Demucs` → `vocals.wav` + `music.wav`. Já responde *tem narração?* e *tem trilha?*.

**3. Transcrição com timestamp por palavra.** `faster-whisper` (`medium` no dia a dia, `large-v3` no passe final) + `WhisperX`.
⚠️ **Não usar a legenda do YouTube:** `timedtext` devolve 0 byte mesmo listando a trilha `pt/asr`.

**4. Cortes e ritmo.** `PySceneDetect` (`detect-adaptive`) → cortes/min, média e mediana de plano, desvio. No Modo B: BPM (`librosa`) e **% de cortes na batida** (±80 ms).

**5. Keyframes + leitura visual — nativa.** 1 frame no meio de cada plano; ler com `Read` **em lotes de 6 a 10** e descrever paleta, enquadramento, tipo de material, estilo de legenda (fonte, peso, contorno, posição, karaokê ou não), overlays e efeitos.

**6. Transições.** Cruzar cortes com keyframes de borda: corte seco, whip pan, zoom, flash, match cut, dissolve. Contar a distribuição — "92 % corte seco, 8 % flash na batida" é acionável.

**7. Áudio: mixagem.** `loudnorm` → LUFS, faixa dinâmica, pico; medir ducking; estimar se a voz é humana, TTS ou processada por IA.

**8. `ANALISE.md`** pela rubrica.

## 1.4 Rubrica do relatório (`references/rubrica-analise.md`)

```markdown
# ANALISE — <título> (<plataforma>)
Fonte · duração · resolução · proporção · views · data

## 1. Veredito em 5 linhas
## 2. Estrutura narrativa   ← tabela com [mm:ss], função e fala
## 3. Roteiro transcrito
## 4. Ritmo de edição       ← cortes/min · média · mediana · % na batida · BPM
## 5. Estilo visual         ← paleta · material · enquadramento · efeitos + keyframes citados
## 6. Transições            ← distribuição + 3 exemplos com timestamp
## 7. Legendas              ← fonte · cor/contorno · posição · safe area · karaokê · palavras/cartela
## 8. Áudio                 ← narração · trilha · LUFS · ducking · SFX
## 9. Fórmula extraída      ← esqueleto reutilizável em tempos relativos + CTA + hashtags
## 10. Como replicar        ← rascunho de videospec.json já preenchido
```

**Regra de qualidade:** toda afirmação de estilo precisa de **timestamp** ou **número**. "Edição dinâmica" é proibido; "34 cortes/min, mediana de 1,8 s" é o padrão.

## 1.5 Ferramentas necessárias

| Ferramenta | Uso | Estado |
|---|---|---|
| `yt-dlp` (novo) | download | ⚠️ substituir a do apt |
| `ffmpeg` | áudio, keyframes, loudnorm | ✅ instalado |
| `faster-whisper` + `WhisperX` | transcrição + palavra | ❌ instalar |
| `Demucs` | separar voz/trilha | ❌ instalar |
| `PySceneDetect` | cortes | ❌ instalar |
| `librosa` / `aubio` | BPM | ❌ instalar |
| `Read` (nativo) | **ver** keyframes | ✅ |
| `chrome-agente` (skill) | conteúdo logado | ✅ |

## 1.6 Como o Claude Code executaria

- **Paralelizar** chamadas independentes no mesmo bloco (transcrição e detecção de cena não dependem uma da outra).
- **Background** (`run_in_background`) para download e Demucs; seguir trabalhando no que não depende deles.
- **Visão em lote**, nunca frame a frame.
- **`chrome-agente`** como caminho próprio para o que exige login.
- **Subagente interno `Explore`** quando houver muitas referências e o interesse for a conclusão.
- **`deepseek-subagent`** para segunda opinião **textual** sobre a fórmula extraída (sem visão).

## 1.7 Dependências / instalação

```bash
# ilustrativo — NÃO executado neste planejamento
uv tool install yt-dlp                     # substitui a versão quebrada do apt
uv tool install "faster-whisper[cli]"
pipx install demucs
pipx install scenedetect
uv tool install auto-editor
sudo apt install rubberband-cli libass-dev
```
Modelo nesta máquina (11 GB RAM, sem GPU): `medium` com `compute_type=int8`; `large-v3` só no passe final.

## 1.8 Limitações

- **Instagram/TikTok exigem o Chrome logado** — a autonomia aqui depende do `chrome-agente` funcionando (CDP no perfil-espelho).
- **Sem julgamento estético absoluto.** A skill mede e compara; o contraste 3,08 M × 14,7 k do RM RAPS, com pipeline idêntico, mostra que a variável decisiva (tema) está fora do alcance da medição.
- **Custo de contexto:** 40 keyframes enchem a janela → limitar a ~15 representativos.
- **Transcrição de música é ruim** → rodar sobre `vocals.wav`.
- **`detect-adaptive` erra em edits com flash constante** → validar por amostragem.

## 1.9 Próximos passos

1. Baixar os 4 vídeos de referência com o `chrome-agente` e fechar as lacunas do README §3.4.
2. Escrever `references/estilos-referencia.md` com os números medidos.
3. Só então redigir o `SKILL.md`, calibrado por dados reais.

---

# SKILL 2 — `video-criacao`

## 2.1 Objetivo

Do briefing ao arquivo publicável, **no estilo medido pela `video-analise`**: roteiro → storyboard por cena → assets → narração → edição → export 9:16 e 16:9.

## 2.2 Quando usar (gatilhos)

- "faz um reel sobre X no estilo daquele vídeo"
- "cria um short de 30s sobre Y"
- "monta o roteiro e o storyboard de ..."
- "transforma esse texto/parecer em vídeo"
- "exporta também em 16:9"

## 2.3 Fluxo passo a passo

1. **Briefing.** Tema, plataforma, duração, referência de estilo, voz. Até 3 perguntas; depois seguir com premissas declaradas.
2. **Roteiro** pela fórmula do Modo A (README §3.2), a ~**2,7 palavras/segundo**. Reel de 30 s ≈ 80 palavras — escrever 200 e "resolver na edição" é o erro clássico.
3. **Storyboard por cena** → `cenas[]` do `videospec.json`.
4. **Assets**, por ordem de custo: material próprio → imagem por API (fal.ai/Replicate) + `zoompan` (resolve ~80 % do Modo A) → vídeo generativo só onde o movimento é o ponto → clipe de anime como último recurso (README §9.1).
5. **Narração.** `edge-tts` (`pt-BR-AntonioNeural` / `FranciscaNeural` / `ThalitaMultilingualNeural`), um `.wav` por cena, ritmo `+8%`. Refazer cena isolada é barato; regenerar tudo, não.
6. **Legendas** transcrevendo a **narração sintetizada** (o TTS muda a duração real) → `.ass` karaokê dentro da safe area (x 100–860, y 300–1450).
7. **Edição.** `ffmpeg`: `concat` → `xfade`/corte seco → `ass` → mix com ducking → `loudnorm` −14 LUFS. Encode com **VAAPI** (`h264_vaapi`). No Modo B, cortes alinhados ao BPM.
8. **Export** 9:16 principal + 16:9 (reenquadrar, **não** *letterbox*). Conferir duração, safe area, LUFS, `faststart`.
9. **👁️ Prova visual própria.** Extrair 6 keyframes do render e **olhar com `Read`** antes de entregar: legenda cortada? texto legível sobre o fundo? enquadramento certo? — autorrevisão nativa, sem pedir a ninguém.

### Identidade visual — feita aqui mesmo

O preset (`jjk-dark`: fonte, cores, contorno, posição, densidade de corte) mora em `references/presets-identidade.md` e é aplicado via `.ass` + filtros do `ffmpeg`. Se algum projeto pedir composição mais elaborada (letra sincronizada de clipe, lower-thirds animados), **este agente instala e usa Remotion por conta própria** (`npx create-video@latest`, render com `--props videospec.json`) — é uma ferramenta do SO como qualquer outra, não um serviço de outro agente.

## 2.4 Ferramentas

`edge-tts` · `ffmpeg` (`concat`, `xfade`, `zoompan`, `ass`, `loudnorm`, `h264_vaapi`) · API de imagem (fal.ai/Replicate) · `faster-whisper` (legendar a narração) · `Read` (prova visual) · Remotion (opcional, instalado pela própria skill).

## 2.5 Como o Claude Code executaria

Escrever o `videospec.json`, rodar o render pelos scripts da própria skill, e **revisar o resultado com os próprios olhos**. Render longo em background. Variações A/B (5 hooks, 3 vozes) saem de um loop em `Bash` reaproveitando as cenas comuns — paralelismo interno, sem terceirizar o lote.

## 2.6 Limitações

- Sem GPU: difusão local está fora; imagem é sempre API paga.
- `xfade` re-encoda tudo — lento em vídeo longo; VAAPI ajuda (com alguma perda frente a `libx264` CRF baixo).
- 16:9 a partir de 9:16 quase sempre exige reenquadrar; sinalizar baixa confiança em vez de entregar recorte ruim.
- TTS não faz entonação de rap: o Modo B segue o pipeline "guia de voz humana + IA" do RM RAPS.
- Fonte precisa estar instalada, senão `libass` cai em fallback silencioso.

## 2.7 Próximos passos

1. Definir o preset `jjk-dark` a partir das medições reais.
2. Produzir **um** Reel completo e comparar lado a lado com o original.
3. Fixar o custo médio por vídeo (imagem + TTS) como teto no `videospec.json`.

---

# SKILL 3 — `video-dublagem`

## 3.1 Objetivo

Trocar o idioma da narração **preservando sincronia e a trilha original**. Direções: pt-BR → en/es e en → pt-BR.

## 3.2 Quando usar (gatilhos)

- "dubla esse vídeo pra inglês/espanhol"
- "faz uma versão em português desse aqui"
- "quero esse reel em 3 idiomas"
- "troca a voz da narração"

## 3.3 Fluxo passo a passo

1. **Separar** com `Demucs` → `vocals.wav` + `music.wav`. A trilha original é preservada — é o que mantém a identidade sonora.
2. **Transcrever** `vocals.wav` com timestamp por palavra.
3. **Segmentar por unidade de fala** (pausa >200 ms), não por frase gramatical.
4. **Traduzir com restrição de duração — o próprio Claude Code traduz.** Cada segmento recebe o orçamento de caracteres do idioma alvo; gerar **3 variantes** (curta/média/longa) para escolher no encaixe. Esta é a camada que mais decide o resultado.
5. **TTS por segmento** (`edge-tts` multi-idioma), medindo a duração real.
6. **Encaixe temporal, em cascata:** (a) variante que encaixa; (b) absorver no silêncio adjacente; (c) `rubberband` até **±10 %**; (d) nova tradução mais curta; (e) marcar para revisão. **A ordem importa** — ir direto ao time-stretch é o que produz dublagem robótica.
7. **Remix:** narração + `music.wav` com ducking → `loudnorm`.
8. **Legendas** no idioma novo, geradas do áudio dublado real.
9. **QA de sincronia:** desvio por segmento, média, p95, pior caso. Meta **≤150 ms**; listar os 5 piores com timestamp.

## 3.4 Ferramentas

`Demucs` · `faster-whisper`/`WhisperX` · **o próprio modelo para tradução** · `edge-tts` (multi-idioma, grátis) ou ElevenLabs Dubbing (pago, resolve sincronia nativamente) · `rubberband` · `ffmpeg`.
⚠️ **XTTS-v2 é CPML — não comercial.** Canal monetizado exige ElevenLabs ou modelo com licença permissiva.

## 3.5 Como o Claude Code executaria

Vantagem própria: **ele mesmo é o tradutor**. Não há chamada externa na etapa mais delicada — traduz com a restrição de duração no contexto, vendo o tom do vídeo inteiro, e itera nos segmentos que estouram. Multi-idioma vira loop reaproveitando Demucs e transcrição, feitos **uma vez**.

## 3.6 Limitações

- **Sem lip-sync.** Irrelevante para narração em off e anime edit; **bloqueante** para talking head em close — e a skill deve avisar ao ser acionada nesse caso.
- **Voz clonada de terceiro exige autorização.**
- **Trocadilho não sobrevive.** "Técnica Amaldiçoada: *Você Que Sabe*" não tem equivalente direto em inglês → **sinalizar**, não inventar.
- **Demucs em CPU é lento** (~5–10× tempo real): Reel de 30 s tranquilo; clipe de 4 min, rodar em background e avisar o tempo.
- **Prosódia:** TTS não reproduz ironia, e o tom das referências é irônico.

## 3.7 Próximos passos

1. Piloto pt→en de um Reel curto, medindo o desvio real.
2. Comparar `edge-tts` × ElevenLabs no mesmo material.
3. Definir a política de trocadilhos e gravar em memória.

---

## 4. Autonomia — nada sai daqui

| Etapa | Como o Claude Code resolve **sozinho** |
|---|---|
| Ver keyframes | `Read` nativo, em lotes |
| Instagram com login | skill `chrome-agente` (Chrome logado, CDP) |
| Lote de vídeos | loop em `Bash` + background + subagentes internos |
| Identidade visual elaborada | `.ass` + filtros; Remotion instalado pela própria skill se precisar |
| Tradução da dublagem | o próprio modelo |
| Revisar o render | `Read` nos keyframes do resultado |
| Ferramenta faltando ou quebrada | escreve/conserta em `~/.claude/skills/<skill>/scripts/` |

O formato comum (README §5) permite **abrir** artefatos produzidos em outro ambiente, mas nada aqui **depende** disso: o pipeline cria a estrutura do zero.

Memória a gravar quando a Fase 0 rodar: presets validados e os bloqueios de plataforma — que mudam e custam tempo toda vez que forem redescobertos.
