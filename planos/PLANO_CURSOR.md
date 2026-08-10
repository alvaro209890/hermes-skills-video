# Plano — Skills de vídeo no **Cursor**

**Princípio:** 🔒 **autonomia total.** O Cursor executa o pipeline inteiro — baixar, transcrever, extrair e **ver** frames, analisar, roteirizar, gerar cenas, narrar, editar, exportar 9:16 e 16:9, e dublar — **sozinho**, dentro do projeto dele. **Zero roteamento para outro agente.**
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
> - [ ] Decisão sobre a licença do Remotion tomada (ver §7 deste plano)

---

## 0. O que o Cursor tem para fechar o pipeline sozinho

| Necessidade do pipeline | Recurso próprio | Observação |
|---|---|---|
| **Rodar yt-dlp, ffmpeg, Demucs** | terminal integrado (o Agent executa comandos) | mesmo SO, mesmas ferramentas |
| **Transcrever** | **`@remotion/install-whisper-cpp`** — instala e roda whisper.cpp **de dentro do projeto Node** | não precisa de nada fora do projeto |
| **Ver keyframes** | modelo do Agent aceita **imagem no contexto** | os `.jpg` extraídos entram na conversa |
| **Instagram com login** | terminal + `yt-dlp --cookies-from-browser chrome` | o Chrome do Álvaro está na mesma máquina |
| **Narração (TTS)** | `edge-tts` via terminal, ou API por `fetch` no Node | |
| **Gerar imagem/vídeo de cena** | API (fal.ai / Replicate) chamada por script do projeto | |
| **Editar e exportar** | **Remotion** (vantagem própria) **+** `ffmpeg` no terminal | Remotion compõe; ffmpeg corta e normaliza |
| **Automatizar** | `.cursor/commands/*.md`, `.cursor/rules/*.mdc`, `AGENTS.md`, background agents | |

**Vantagem própria (não exclusividade):** é o único onde o vídeo é **visto enquanto é construído**. Com Remotion, a composição vira React+TypeScript e o `remotion studio` mostra preview ao vivo com timeline e scrubbing — o Agent edita o `.tsx`, o hot-reload atualiza, o Álvaro vê na hora.

| | `ffmpeg` puro | Remotion (aqui) |
|---|---|---|
| Iterar em timing/animação | render completo a cada tentativa | preview instantâneo |
| Legenda karaokê | montar `.ass` na mão | componente React com estado por frame |
| Revisão humana | só no arquivo final | contínua, no Studio |
| Versionamento | comando gigante e opaco | componentes em git, com diff legível |

**Divisão interna (dentro do próprio Cursor):** `ffmpeg` para o mecânico (baixar, cortar, separar faixas, normalizar, dublar); **Remotion para a identidade visual** (legendas animadas, lower-thirds, letra sincronizada, cartelas de CTA).

**Escolha o Cursor quando** quiser **ver** o vídeo sendo montado e iterar no visual com o Álvaro junto.

---

## 1. O que criar

```
~/Documentos/Video_Studio/studio/          # projeto próprio, versionado em git
├── .cursor/
│   ├── rules/
│   │   ├── video-identidade.mdc     # alwaysApply: paleta, fonte, safe area, dos & don'ts
│   │   ├── remotion-padroes.mdc     # globs: src/**/*.tsx
│   │   └── videospec-contrato.mdc   # como ler/escrever o videospec.json
│   ├── commands/
│   │   ├── analisar.md              # /analisar <url>  ← pipeline completo de análise
│   │   ├── novo-reel.md             # /novo-reel <slug>
│   │   ├── legendas-karaoke.md
│   │   ├── dublar.md                # /dublar <slug> <idioma>
│   │   └── render-tudo.md           # 9:16 + 16:9
│   └── mcp.json                     # opcional
├── AGENTS.md
├── scripts/                         # ⭐ pipeline próprio (Node/TS + chamadas a ffmpeg)
│   ├── doctor.ts  fetch.ts  transcribe.ts  scenes.ts  keyframes.ts
│   ├── tts.ts     dub/                     # separate · translate · fit · mix · qa
├── src/
│   ├── Root.tsx                     # <Composition> 9:16 e 16:9
│   ├── compositions/ReelModoA.tsx · ClipeModoB.tsx
│   ├── cenas/  ClipeVideo · ImagemKenBurns · CartelaTexto · CTA
│   ├── legendas/ LegendaKaraoke.tsx · estilos.ts
│   ├── transicoes/ index.ts
│   └── design/ tokens.ts            # ⭐ identidade (gerada pela própria análise)
├── refs/<slug>/                     # análises feitas aqui
├── specs/<slug>.json
└── public/
```

---

# SKILL 1 — `video-analise`

## 1.1 Objetivo

Analisar um vídeo **do zero, dentro do projeto**: baixar, transcrever, medir ritmo, **ver os frames**, produzir `refs/<slug>/ANALISE.md` com `[mm:ss]` — e, no passo seguinte que é a força deste ambiente, **converter a análise em `src/design/tokens.ts`**, tornando o estilo medido imediatamente visível no Studio.

## 1.2 Quando usar (gatilhos)

- "/analisar <url>"
- "analisa esse reel e aplica o estilo no nosso template"
- "por que a nossa legenda não fica igual à dele"
- "compara nosso render com a referência"
- "extrai o ritmo e a estrutura desse vídeo"

## 1.3 Fluxo passo a passo

**0. `doctor`** (`scripts/doctor.ts`): `yt-dlp` **novo** (a do apt está quebrada — README §3.4), `ffmpeg`, whisper.cpp instalado por `@remotion/install-whisper-cpp`, `Demucs`, `PySceneDetect`, Node, disco.

**1. Baixar** — terminal → `yt-dlp` (com `--cookies-from-browser chrome` para Instagram/TikTok, resolvendo o login sem sair daqui).

**2. Áudio e faixas** — `ffmpeg` + `Demucs` → `vocals.wav`, `music.wav`.

**3. Transcrever** — `@remotion/install-whisper-cpp` baixa o modelo e transcreve **dentro do projeto**, com timestamps por palavra prontos para alimentar `@remotion/captions`. Vantagem prática: a transcrição já sai no formato que o render consome.
⚠️ **Não usar a legenda do YouTube:** `timedtext` devolve 0 byte.

**4. Cortes e ritmo** — `PySceneDetect` → cortes/min, média e mediana de plano; no Modo B, BPM e **% de cortes na batida**.

**5. Keyframes** — `ffmpeg` extrai 1 frame por plano (~15 representativos).

**6. 👁️ Ver os frames** — os `.jpg` são levados ao contexto do Agent, que descreve paleta, enquadramento, tipo de material, **estilo de legenda** (fonte, peso, contorno, posição, karaokê) e efeitos. Análise visual **feita aqui**.

**7. Áudio** — `loudnorm` → LUFS, ducking, tipo de voz.

**8. `ANALISE.md`** pela rubrica comum (veredito, estrutura com `[mm:ss]`, roteiro, ritmo, estilo, transições, legendas, áudio, fórmula extraída, rascunho de `videospec.json`).

**9. → `tokens.ts`** — o passo que só existe bem aqui: transformar as medições em preset (`jjkDark`), montar uma composição de **comparação lado a lado** (keyframe da referência × nosso render no mesmo instante) e iterar no Studio até bater.

## 1.4 Ferramentas

`yt-dlp` · `ffmpeg` · `@remotion/install-whisper-cpp` · `Demucs` · `PySceneDetect` · `librosa` · visão do próprio Agent · `remotion still` (frame único para comparar sem render completo) · `remotion studio`.

## 1.5 Como o Cursor executaria

Agent mode com o Studio aberto ao lado. Ciclo: script baixa e mede → Agent lê os frames → escreve `ANALISE.md` → gera `tokens.ts` → hot-reload → Álvaro diz "contorno mais grosso" → ajusta. **Loop de segundos.**

`.cursor/rules/video-identidade.mdc` em `alwaysApply: true` faz todo trabalho no projeto herdar a identidade sem repetir no prompt.

## 1.6 Limitações

- **Requer o app aberto** — sem uso headless na prática (background agents ajudam, mas o Studio é GUI).
- **Lote grande é desconfortável** aqui: dá para rodar um loop de scripts, mas ler 200 frames no contexto do Agent é caro. Para volume, limitar a leitura visual a uma amostra.
- **RAM:** Cursor + Node + Chromium do Studio em 11 GB é apertado.

## 1.7 Próximos passos

1. Rodar a análise dos 4 vídeos de referência e fechar as lacunas do README §3.4.
2. Criar `tokens.ts` com o preset `jjk-dark`.
3. Montar a composição de comparação lado a lado.

---

# SKILL 2 — `video-criacao`

## 2.1 Objetivo

Do briefing ao arquivo final, com **identidade visual de verdade**: legenda karaokê palavra-a-palavra, transições animadas, cartelas e CTA — em 9:16 e 16:9.

## 2.2 Quando usar (gatilhos)

- "/novo-reel <slug>"
- "faz um reel sobre X no estilo do <slug>"
- "a legenda tem que acender palavra por palavra"
- "faz o clipe com a letra sincronizada" ← **caso de ouro do Modo B**
- "cria a abertura/vinheta do canal"

## 2.3 Fluxo passo a passo

1. **Briefing e roteiro** pela fórmula do Modo A (README §3.2), a ~**2,7 palavras/segundo** (Reel de 30 s ≈ 80 palavras).
2. **`specs/<slug>.json`** — passado ao Remotion via `--props`, sem duplicar dados.
3. **Assets:** imagem por API chamada de `scripts/`, movimento por Ken Burns (`interpolate`) — resolve ~80 % do Modo A; vídeo generativo só onde o movimento é o ponto; clipe de anime como último recurso (README §9.1).
4. **Narração** — `edge-tts` via `scripts/tts.ts`, um arquivo por cena, com a **duração real** devolvida ao spec (o TTS quase nunca entrega o tempo previsto).
5. **Legendas** — transcrever a narração sintetizada com whisper.cpp → `@remotion/captions` (`createTikTokStyleCaptions`), o pacote oficial para esse estilo.
6. **Composição** — `calculateMetadata` define a duração a partir do spec (nada de hardcode); `<Sequence>` por cena; `<OffthreadVideo>` / `<Img>` / cartela conforme `visual.tipo`; transições com `@remotion/transitions` (`TransitionSeries`).
7. **Sincronizar com a batida** (Modo B) — `@remotion/media-utils` (`getAudioData`, `visualizeAudio`): flash e zoom **na batida**, waveform reativa.
8. **Preview no Studio** e ajuste com o Álvaro.
9. **Render** das duas composições:
   ```bash
   # ilustrativo
   npx remotion render ReelModoA out/final_9x16.mp4 --props=specs/<slug>.json
   npx remotion render ReelModoA_16x9 out/final_16x9.mp4 --props=specs/<slug>.json
   ```
10. **Passe final de áudio** — `ffmpeg loudnorm` (−14 LUFS, pico −1 dBTP) no terminal.
11. **Verificação** — `ffprobe`: resolução, proporção, duração, LUFS, `faststart`; e leitura de 4 keyframes do render pelo Agent (legenda cortada? safe area?).

## 2.4 Ferramentas necessárias

| Pacote | Para quê |
|---|---|
| `remotion`, `@remotion/cli` | núcleo e Studio |
| `@remotion/captions` | legendas estilo TikTok/Reels |
| `@remotion/transitions` | transições declarativas |
| `@remotion/media-utils` | dados de áudio, waveform, reação à batida |
| `@remotion/install-whisper-cpp` | transcrição dentro do projeto |
| `@remotion/layout-utils` | `fitText` — texto que precisa caber |
| `@remotion/google-fonts` | tipografia sem CDN |
| `@remotion/lambda` *(opcional)* | render em nuvem quando o notebook não der conta |
| `ffmpeg` / `ffprobe` | corte, mix, `loudnorm`, verificação |
| `edge-tts` | narração |

⚠️ **Licença Remotion:** gratuita para indivíduos e empresas pequenas; acima de um limite de porte exige licença paga da Remotion Company. **Verificar os termos vigentes antes de uso comercial** — é a única peça do stack com essa condição. Alternativa sempre disponível dentro do próprio Cursor: renderizar com `ffmpeg` + `.ass`.

## 2.5 Como o Cursor executaria

- **Agent mode** com `.cursor/rules/remotion-padroes.mdc` restrito por `globs: src/**/*.tsx`.
- **Comandos slash** para os fluxos repetidos.
- **TypeScript como rede de segurança:** tipar o `VideoSpec` faz mudança de formato virar erro de compilação.
- **`AGENTS.md`** com as regras invioláveis (safe area, nunca hardcodar duração, sempre ler do spec).
- **Background agents** para render longo, com o Studio livre.

## 2.6 Limitações

- **Render em CPU é lento** — Remotion roda Chromium headless por frame; 30 s a 30 fps = 900 frames. Mitigar com `--concurrency`, `remotion still` para iterar, e `@remotion/lambda` para volume.
- **Vídeo pesado dentro do Remotion** sofre: pré-cortar com `ffmpeg` e compor os trechos.
- **Licença** (acima).
- **É GUI** — não serve como serviço automático; é estação de trabalho.

## 2.7 Próximos passos

1. Criar o projeto (`npx create-video@latest`) com as duas composições e o `VideoSpec` tipado.
2. Implementar `LegendaKaraoke` e validar contra a referência medida.
3. Medir o tempo de render de um Reel de 30 s nesta máquina — decide se Lambda é necessário.

---

# SKILL 3 — `video-dublagem`

## 3.1 Objetivo

Dublar **inteiro, aqui**: separar faixas, traduzir com sincronia, sintetizar, encaixar, remixar — e ainda resolver a camada visual da versão dublada (legendas, textos de tela e CTA no idioma novo).

## 3.2 Quando usar (gatilhos)

- "/dublar <slug> en"
- "dubla isso pra inglês/espanhol"
- "faz as 3 versões de idioma a partir do mesmo template"
- "tem texto na tela em português no vídeo dublado"

## 3.3 Fluxo passo a passo

1. **Separar** — `Demucs` via terminal → `vocals.wav` + `music.wav` (trilha preservada).
2. **Transcrever** `vocals.wav` com whisper.cpp, timestamps por palavra.
3. **Segmentar por unidade de fala** (pausa >200 ms).
4. **Traduzir com restrição de duração — o próprio Agent traduz**, gerando 3 variantes (curta/média/longa) por segmento com o orçamento de caracteres do idioma alvo.
5. **TTS por segmento** (`scripts/tts.ts`), medindo a duração real.
6. **Encaixe em cascata:** variante que encaixa → silêncio adjacente → `rubberband` até **±10 %** → nova tradução mais curta → marcar para revisão.
7. **Remix** narração + `music.wav` com ducking → `loudnorm`.
8. **Camada visual localizada** — a parte que fica especialmente boa aqui: a mesma composição parametrizada por `idioma` troca legendas, `texto_tela` e CTA **preservando o layout**. O ponto que quase sempre quebra é o comprimento (inglês mais curto, espanhol e alemão mais longos) → resolver com `fitText` (`@remotion/layout-utils`) e limite de linhas.
9. **Renderizar N idiomas** do mesmo código, com `--props` diferentes.
10. **QA de sincronia:** desvio por segmento, média, p95, pior caso. Meta **≤150 ms**; listar os 5 piores.

## 3.4 Ferramentas

`Demucs` · whisper.cpp (`@remotion/install-whisper-cpp`) · **o próprio Agent** para tradução · `edge-tts` (ou ElevenLabs) · `rubberband-cli` · `ffmpeg` · `@remotion/captions` + `@remotion/layout-utils` + `@remotion/google-fonts` (cobertura de acentuação e outros alfabetos).
⚠️ XTTS-v2 é CPML (não comercial); voz clonada de pessoa real exige autorização.

## 3.5 Como o Cursor executaria

Scripts do projeto fazem o pesado; o Agent traduz e ajusta o layout; o Studio permite **conferir cada idioma visualmente** antes de exportar — vantagem real, porque erro de layout em idioma que o Álvaro não fala passa despercebido em qualquer outro fluxo.

## 3.6 Limitações

- **Demucs em CPU é lento** (~5–10× tempo real).
- **Sem lip-sync.**
- **Alfabetos não-latinos** exigem fonte com cobertura e podem quebrar o layout.
- **Trocadilho não sobrevive** — sinalizar, não inventar.
- **Render N idiomas** multiplica o tempo de Chromium.

## 3.7 Próximos passos

1. Tipar `idioma` no `VideoSpec` e parametrizar legendas e textos de tela.
2. Testar `fitText` com espanhol (o caso que mais estoura).
3. Script npm de dublagem + render em lote por idioma.

---

## 4. Autonomia — nada sai daqui

| Etapa | Como o Cursor resolve **sozinho** |
|---|---|
| Baixar (inclusive com login) | terminal + `yt-dlp --cookies-from-browser chrome` |
| Transcrever | `@remotion/install-whisper-cpp`, dentro do projeto |
| Ver keyframes | imagens no contexto do Agent |
| Analisar ritmo/áudio | `PySceneDetect`, `librosa`, `loudnorm` via terminal |
| Identidade visual | `tokens.ts` gerado da própria análise |
| Narração | `edge-tts` por `scripts/tts.ts` |
| Editar/exportar | Remotion + `ffmpeg` |
| Dublar | Demucs + tradução do próprio Agent + `rubberband` |
| Verificar o resultado | `ffprobe` + leitura de keyframes + Studio |

O formato comum (README §5) permite **abrir** um `ANALISE.md` ou `videospec.json` vindo de outro ambiente — mas nada aqui **depende** disso. O projeto cria tudo do zero.
