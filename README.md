# hermes-skills-video

Três skills de vídeo para o **Hermes** — o assistente que o Álvaro opera **pelo WhatsApp** —
mais o planejamento completo que as originou.

O caso de ouro: *"vi um Reel no celular, mandei o link, o vídeo chegou pronto"*.

| Skill | O que faz |
|---|---|
| [`video-analise`](skills/video-analise/) | download seguro + cortes/BPM/LUFS/true peak + contato de frames com evidências |
| [`video-criacao`](skills/video-criacao/) | briefing → cenas/painéis → voz Edge processada → beat/legendas → MP4 9:16/16:9 validado |
| [`video-dublagem`](skills/video-dublagem/) | encaixe Rubber Band ±10% e QA ≤150 ms; pipeline integral requer Demucs |

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

## Estado atual: **PIPELINE LOCAL V3** (2026-08-10)

As três skills passaram no validador. Análise técnica e criação local estão operacionais; a
dublagem já encaixa/valida segmentos, mas o fluxo integral continua bloqueado sem Demucs.

| Peça | Estado |
|---|---|
| Doctor por perfil (`analise`, `criacao`, `dublagem`) | ✅ filtro Rubber Band detectado corretamente |
| Downloader | ✅ valores obrigatórios, slug confinado, URL normalizada, yt-dlp atual |
| Análise técnica | ✅ cortes, BPM, LUFS/LRA/TP e folha de contato sem dependências pesadas |
| Criação | ✅ voz rap, grade de beat, painéis, ASS, mix/master, H.264/AAC e QA |
| Dublagem | ✅ encaixe por segmento; ⚙️ separação/remix dependem de Demucs |
| Exemplo Gojo v3 | ✅ scripts/textos reproduzíveis; mídias protegidas excluídas |

### `doctor.sh`

Roda **antes** de prometer resultado — mesmo padrão do `imap doctor`. Separa o que bloqueia agora
(**base**) do que só importa no pipeline completo, e **não instala nada**: reporta e sai.

```bash
skills/video-analise/scripts/doctor.sh --perfil analise
skills/video-criacao/scripts/doctor.sh --json
skills/video-dublagem/scripts/doctor.sh --curto
```

Verifica `ffmpeg` (incluindo filtro Rubber Band), `yt-dlp`, TTS, Demucs e dependências por
perfil, além da **presença** — nunca o valor — das chaves em `~/.hermes/.env`.

As skills `video-criacao` e `video-dublagem` têm um wrapper que chama o doctor canônico da
`video-analise` — um diagnóstico só, sem lógica duplicada.

### Scripts principais

```bash
skills/video-analise/scripts/baixar-video.sh <URL> [--slug s] [--cookies chrome] [--audio-so] [--dry-run]
skills/video-analise/scripts/analisar-referencia.py video.mp4 analise/ --segundos 35
skills/video-criacao/scripts/processar-voz-rap.sh linha.mp3 linha.wav -1.5 1.0
skills/video-criacao/scripts/calcular-grade.py 95 30
skills/video-criacao/scripts/validar-export.sh final.mp4
skills/video-dublagem/scripts/encaixar-fala.sh fala.wav fala_fit.wav 2.850
```

Os detalhes do preset vocal, grade RM RAPS e comandos exatos estão em
[`rap-v3-modelos.md`](skills/video-criacao/references/rap-v3-modelos.md). O caso reproduzível,
sem mídia protegida, está em [`examples/gojo-v3/`](examples/gojo-v3/).

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
9. **TTS Edge costuma decodificar a 24 kHz.** Aplicar `asetrate=48000*fator` sem resample
   encurta a fala drasticamente; usar `aresample=48000` + Rubber Band/formante.
10. **AAC pode ultrapassar o WAV em vários dBTP.** Medir o MP4 decodificado e deixar margem.
11. `--slug`/`--cookies` sem valor causavam loop, e `../` escapava de `entradas/`; ambos têm
    testes de regressão e retornam código 2.

---

## Decisões que moldam o projeto

Tomadas pelo Álvaro em 2026-08-09. Detalhe em [`planos/PLANO_HERMES.md` §7](planos/PLANO_HERMES.md).

- **Custo zero.** Voz = Edge TTS. Rap BR começa por `en-US-AndrewMultilingualNeural` +15%,
  Rubber Band −1,5 st; Francisca segue padrão de narração comum. Sem ElevenLabs/API paga.
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
├── video-analise/    doctor · downloader seguro · análise técnica · references
├── video-criacao/    voz rap · animação · grade · validação · recipes
└── video-dublagem/   doctor por perfil · encaixe/QA · sincronia
examples/gojo-v3/     scripts e textos do caso validado, sem mídia protegida
```

Sem segredos, sem credenciais: o `doctor.sh` verifica apenas a **presença** de variáveis de
ambiente e nunca lê ou imprime valores.
