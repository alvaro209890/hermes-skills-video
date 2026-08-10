# hermes-skills-video

Três skills de vídeo para o **Hermes** — o assistente que o Álvaro opera **pelo WhatsApp** —
mais o planejamento completo que as originou.

O caso de ouro: *"vi um Reel no celular, mandei o link, o vídeo chegou pronto"*.

| Skill | O que faz |
|---|---|
| [`video-analise`](skills/video-analise/) | link ou vídeo → baixa, transcreve, extrai frames, **vê** os frames → `ANALISE.md` com `[mm:ss]` |
| [`video-criacao`](skills/video-criacao/) | briefing → roteiro → cenas (`image_gen` + `zoompan`) → narração (edge TTS) → legendas → MP4 **9:16 e 16:9** |
| [`video-dublagem`](skills/video-dublagem/) | troca o idioma preservando a trilha original e a sincronia (meta: desvio **≤150 ms**) |

As três compartilham um **protocolo de conversa no WhatsApp**: aceite em segundos, progresso por
marco, no máximo **3 perguntas por vídeo**, entrega como anexo nativo. O protocolo está em
[`skills/video-analise/references/protocolo-whatsapp.md`](skills/video-analise/references/protocolo-whatsapp.md)
— um arquivo só, para as três não divergirem.

---

## 🚦 Fases e o gate

O plano cobre **cinco** agentes (Hermes, Claude Code, Cursor, OpenCode, Codex), cada um capaz de
rodar o pipeline inteiro sozinho. Mas eles são construídos **em série**, não em paralelo:

> ### FASE 1 (atual) — **só o Hermes**
> Desenvolver, testar e validar 100% os três eixos, **operando pelo WhatsApp**.
>
> ### 🔒 GATE
> A Fase 2 não começa enquanto os critérios de
> [`planos/PLANO_HERMES.md` §6](planos/PLANO_HERMES.md) não estiverem todos marcados **e** o
> Álvaro não disser *"tá validado"* depois de rodar os três eixos pelo celular.
>
> ### ⛔ FASE 2 — os outros quatro
> Congelados até o gate abrir.

**Por que em série:** o pipeline é o mesmo nos cinco. Tudo que for descoberto construindo o
Hermes — o prompt de visão que funciona, a cascata de sincronia calibrada, os campos que faltam
no `videospec.json`, o tempo real de cada etapa — chega aos outros quatro já resolvido.
Construir os cinco juntos seria descobrir os mesmos erros cinco vezes.

---

## 🚧 Estado atual: **BASE** (2026-08-10)

Só a base está implementada. Isso é escopo, não pendência: o pipeline é a etapa seguinte.

| Peça | Estado |
|---|---|
| `scripts/doctor.sh` — diagnóstico do ambiente | ✅ funciona (3 modos), **executado** |
| `scripts/baixar-video.sh` — download com os gotchas conhecidos | ✅ funciona, **download real validado** |
| `SKILL.md` × 3 + 7 arquivos de `references/` | ✅ escritos |
| transcrição, cortes, keyframes, visão, roteiro, TTS, render, dublagem | ⛔ **não implementado** |

### `doctor.sh`

Roda **antes** de prometer resultado — mesmo padrão do `imap doctor`. Separa o que bloqueia agora
(**base**) do que só importa no pipeline completo, e **não instala nada**: reporta e sai.

```bash
skills/video-analise/scripts/doctor.sh            # relatório completo
skills/video-analise/scripts/doctor.sh --curto    # cabe numa mensagem de WhatsApp
skills/video-analise/scripts/doctor.sh --json     # para consumo por script
```

Verifica `ffmpeg` (filtros + VAAPI), `yt-dlp`, `faster-whisper`, `edge-tts`, `tesseract`,
`Demucs`, `PySceneDetect`, `librosa`, `rubberband`, `piper`, runtimes, disco e a **presença**
(nunca o valor) das chaves em `~/.hermes/.env`. Sai `1` se faltar algo da base.

As skills `video-criacao` e `video-dublagem` têm um wrapper que chama o doctor canônico da
`video-analise` — um diagnóstico só, sem lógica duplicada.

### `baixar-video.sh`

```bash
skills/video-analise/scripts/baixar-video.sh <URL> [--slug s] [--cookies chrome] [--audio-so] [--dry-run]
```

Baixa para `~/Documentos/Video_Studio/entradas/<slug>/` (`fonte.*` + `fonte.info.json` +
`download.log`), normaliza a URL (`?igsh=`, `&list=`, `?si=`), deriva slug legível por plataforma
(`ig-…`, `yt-…`, `tt-…`) e diagnostica a falha em vez de só devolver um código de erro.

---

## ⚠️ Gotchas verificados (custam horas se redescobertos)

1. **`yt-dlp` do apt (2024.04.09) está quebrado para YouTube** — `Requested format is not
   available`, extractor desatualizado. O script **recusa** links do YouTube nessa versão e manda
   `uv tool install yt-dlp`. Nunca confiar no pacote do apt.
2. **O `timedtext` do YouTube devolve 0 byte** mesmo listando a trilha `pt/asr` — a plataforma
   passou a exigir *proof-of-origin token*. Legenda automática do YouTube **nunca** serve:
   transcrição própria com `faster-whisper`, sempre.
3. **Instagram exige sessão logada.** Caminho: `--cookies-from-browser`; se falhar, o Hermes abre
   a tool `browser` na sessão logada. Nunca responder "não consegui".
4. **Heredoc dispara aprovação no Hermes** (`approvals.mode: manual`, janela de 60 s) — inviável
   para quem está no celular. Por isso os scripts são **arquivos**, executados como arquivo.
5. **`ffmpeg … | grep -q` sob `set -o pipefail` dá falso-negativo silencioso** — o `grep -q` sai
   cedo, o ffmpeg morre de SIGPIPE (141) e o `&&` nunca dispara. Capture a lista numa variável e
   grepe a variável. (Bug real, encontrado e corrigido ao escrever o `doctor.sh`.)
6. **`vision_analyze` devolve texto, não pixels** — uma pergunta nova sobre o mesmo frame custa
   uma chamada nova. Peça tudo num prompt só.
7. **Job longo tem que ser processo em background** (`gateway_timeout` 3600 s) que avisa por
   `hermes send --to whatsapp` — isso funciona fora do turno do agente.
8. **`delegation`:** o paralelismo real é **3** (`max_concurrent_children`), não N.

---

## Decisões que moldam o projeto

Tomadas pelo Álvaro em 2026-08-09. Detalhe em [`planos/PLANO_HERMES.md` §7](planos/PLANO_HERMES.md).

- **Custo zero.** Voz = **edge TTS** (`pt-BR-FranciscaNeural`). Sem ElevenLabs, sem API paga de voz.
- **`image_gen` + `zoompan`** (Ken Burns) é o padrão de cena — resolve ~80 % do formato Reel e
  custa nada. `video_gen` não existe no toolset `whatsapp`.
- **Job pesado roda local**, com o caminho preparado para priorizar a máquina mais potente da rede
  quando estiver ligada.
- **Fallback de visão** (Grok 4.5 via API do Cursor) fica **previsto e não configurado** — a
  decisão foi deixar a config prevista, não implementá-la agora.

---

## Instalação

As skills vivem em `~/.hermes/skills/`:

```bash
git clone https://github.com/alvaro209890/hermes-skills-video.git
cp -r hermes-skills-video/skills/video-* ~/.hermes/skills/
~/.hermes/skills/video-analise/scripts/doctor.sh
```

O `doctor.sh` dirá o que falta. **Ele não instala nada de propósito** — quem decide instalar é
uma pessoa.

## Estrutura

```
planos/            os 6 documentos de planejamento (README = fases/gate, PLANO_HERMES = Fase 1)
skills/
├── video-analise/    SKILL.md · scripts/{doctor,baixar-video}.sh · references/×3
├── video-criacao/    SKILL.md · scripts/doctor.sh (wrapper)      · references/×4
└── video-dublagem/   SKILL.md · scripts/doctor.sh (wrapper)      · references/×2
```

Sem segredos, sem credenciais: o `doctor.sh` verifica apenas a **presença** de variáveis de
ambiente e nunca lê ou imprime valores.
