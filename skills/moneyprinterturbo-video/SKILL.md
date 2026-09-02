---
name: moneyprinterturbo-video
description: "Use quando o Álvaro pedir para criar, gerar, refazer, localizar, validar ou entregar vídeos (Shorts verticais ou Longos de 3 a 35 min) pelo site video.cursar.space, pelo MoneyPrinterTurbo deste PC, ou por seu pipeline sem interface. Opera a instalação real em /home/acer/Projetos/MoneyPrinterTurbo, prioriza o CLI local, usa padrões brasileiros testados, acompanha tarefas até o MP4 e nunca publica em rede social sem autorização humana explícita."
version: 1.1.0
author: Hermes-acer/videos
license: MIT
metadata:
  hermes:
    tags: [video, moneyprinterturbo, streamlit, shorts, reels, long-video, cli]
    related_skills: [video-criacao, moneyprinterturbo-operacao]
---

# MoneyPrinterTurbo — criação de vídeo (Shorts e Vídeos Longos)

## Visão geral

Esta skill opera o sistema publicado em **https://video.cursar.space**. A WebUI é Streamlit,
mas o caminho preferido do agente é o CLI do mesmo projeto: é mais estável, reproduzível e
não depende do estado visual do navegador.

| Item | Valor observado e validado em 2026-08-28 |
|---|---|
| PC | `acer` |
| Projeto | `/home/acer/Projetos/MoneyPrinterTurbo` |
| WebUI local | `http://127.0.0.1:8501` |
| Serviço | `moneyprinter-webui.service` |
| Túnel | `video-tunnel.service` |
| Site público | `https://video.cursar.space` |
| Versão | MoneyPrinterTurbo `1.3.5` + modo longo nativo |
| Saídas | `storage/tasks/<UUID>/final-*.mp4` |
| Execução preferida | `~/.hermes/skills/media/moneyprinterturbo/scripts/mpt.py` → `cli.py` |

## Quando usar

- “crie um vídeo nesse site”, “gere no video.cursar.space” ou “use o MoneyPrinterTurbo”;
- geração de **Shorts** (verticais 9:16) ou **Vídeos Longos** (horizontais 16:9, 3 a 35 minutos) com roteiro em capítulos por LLM, Edge TTS, legenda sincronizada e BGM;
- localizar, listar, inspecionar ou validar vídeos já gerados pelo sistema;
- gerar só roteiro/outline, termos, áudio, legenda ou materiais como etapa intermediária;
- gerar Shorts e Longos com **alinhamento semântico de cenas e beats narrativos** (padrão do `mpt.py`);
- substituir o pipeline legado do NotebookLM por geração 100% automatizada e limpa.

## Regra de decisão: CLI primeiro

1. **CLI (`mpt.py`)** para agentes, cronjobs diários, automação e tarefas reproduzíveis.
2. **WebUI** para o Álvaro ajustar visualmente presets, ouvir voz ou acompanhar o Gerenciador de tarefas.

---

## 🚀 Como Executar

### 1. Shorts / Reels / TikTok (padrão vertical 9:16)

```bash
~/.hermes/skills/media/moneyprinterturbo/scripts/mpt.py \
  --subject "<tema do short>" \
  --language pt-BR \
  --aspect 9:16 \
  --source pexels
# --semantic-matching já é o padrão; não passar --no-semantic-matching
```

### 2. Vídeos Longos (YouTube horizontal 16:9, 3 a 35 min)

```bash
# Geração completa com roteiro em capítulos gerado por LLM:
~/.hermes/skills/media/moneyprinterturbo/scripts/mpt.py \
  --long --duration 10 \
  --subject "Como o bug do ano 2000 foi evitado por engenheiros" \
  --voice pt-BR-ThalitaMultilingualNeural-Female

# Com roteiro próprio estruturado (pula LLM, particiona semântica de capítulos):
~/.hermes/skills/media/moneyprinterturbo/scripts/mpt.py \
  --long --duration 15 --script-file /caminho/roteiro.txt --aspect 16:9

# Em duas etapas (gerar capítulos/outline primeiro para inspeção):
~/.hermes/skills/media/moneyprinterturbo/scripts/mpt.py \
  --long --duration 12 --subject "História do Unix e Linux" --stop-at script
```

---

## ⚙️ Padrões e Regras do Modo Longo (`--long`)

| Item | Padrão no Modo Longo |
|---|---|
| Aspecto | `16:9` (horizontal) automático |
| Duração | 3 a 35 minutos (`--duration <min>`). >35 min é rejeitado na CLI. |
| Capítulos | ~1 capítulo a cada 2,5 min (`150s`), com continuidade temática |
| Materiais | Baixados por cena (alinhamento semântico) com termos contextuais e filtro anti-anacronismo |
| Cortes | Timeline de slots 1:1 com a narração, sem drift (`--semantic-matching`, padrão ligado) |
| Normalização de Áudio | **−14 LUFS** integrada nativamente (atende padrão YouTube) |
| Pós-processamento | **Nenhum necessário.** Não usar `tratar-notebooklm-video.py`. |

---

## 📦 Saídas e Entrega

Os arquivos gerados são salvos em:
`/home/acer/Projetos/MoneyPrinterTurbo/storage/tasks/<task_id>/`

- `final-1.mp4`: Vídeo completo final em alta qualidade (H.264 High Profile, AAC 48 kHz, −14 LUFS).
- `script.json`: Roteiro, minutagem dos capítulos e fontes de materiais.
- `semantic_plan.json`: Cenas com timestamps e prompts visuais (anti-anacronismo).
- `scene_materials_manifest.json`: Clipe escolhido por cena.

Para entregar o vídeo no chat:
Inclua `MEDIA:/home/acer/Projetos/MoneyPrinterTurbo/storage/tasks/<task_id>/final-1.mp4` na resposta.

---

## ⚠️ Armadilhas e Regras Críticas

1. **Tempo de Render:** Vídeos longos exigem processamento pesado (~25 min para 5 min de vídeo). Execute como processo monitorado ou em background.
2. **Fila única:** `max_concurrent_tasks=1` é intencional para isolar configurações. Nunca dispare dois renders simultâneos.
3. **Não usar `tratar-notebooklm-video.py`:** Esse script legado servia apenas para cortar marca d'água e tela final do NotebookLM; aplicá-lo nos vídeos do MPT degrada o áudio e vídeo à toa.
4. **Créditos:** Copie as fontes listadas em `script.json` para a descrição do YouTube junto com as fontes factuais.
5. **NotebookLM como Fallback:** O NotebookLM permanece apenas como alternativa de emergência em caso de falha persistente de estoque/TTS.
6. **Alinhamento semântico é o padrão:** `mpt.py` envia `--semantic-matching` salvo `--no-semantic-matching`. Shorts e Longos do canal devem usar cenas com timestamps, prompts anti-anacronismo e timeline sem drift.
