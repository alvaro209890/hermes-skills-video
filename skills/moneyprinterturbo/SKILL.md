---
name: moneyprinterturbo
description: "Gera vídeos automáticos curtos (Shorts/Reels/TikTok) e longos (3 a 35 min) usando a infraestrutura do MoneyPrinterTurbo (local no acer e exposto em video.cursar.space). Cria roteiro por LLM em capítulos ou Shorts, narração TTS em pt-BR (Edge TTS), alinhamento semântico de clipes às cenas e beats da narração (padrão), busca de vídeos de estoque (Pexels/Pixabay/Coverr/Seedance) ou materiais locais, geração de legendas sincronizadas, normalização para -14 LUFS e mixagem de música de fundo."
---

# MoneyPrinterTurbo (MPT) — Gerador Automático de Vídeos

Esta skill opera a ferramenta **MoneyPrinterTurbo** que roda localmente no **acer** (`/home/acer/Projetos/MoneyPrinterTurbo`) e tem sua WebUI (Streamlit) exposta em **`https://video.cursar.space`** (porta `8501`).

Você **não precisa usar o navegador ou a interface WebUI**: pode disparar e controlar a geração diretamente pelo script wrapper ou CLI local com retorno de arquivos, logs e progresso completo.

---

## 🚀 Como Executar

O script helper já resolve o ambiente virtual, as variáveis de ambiente, configurações de LLM (conectadas ao 9Router da frota) e as chaves de estoque (Pexels/Pixabay):

```bash
# 1. Short a partir de tema/assunto (alinhamento semântico LIGADO por padrão):
~/.hermes/skills/media/moneyprinterturbo/scripts/mpt.py --subject "Como organizar o dia para ter mais foco"

# 2. Vídeo Longo (ex: 10 minutos para YouTube horizontal 16:9):
~/.hermes/skills/media/moneyprinterturbo/scripts/mpt.py \
  --long --duration 10 \
  --subject "O bug do Ariane 5: 37 segundos e 370 milhões de dólares" \
  --voice pt-BR-ThalitaMultilingualNeural-Female

# 3. Vídeo Longo com roteiro próprio estruturado:
~/.hermes/skills/media/moneyprinterturbo/scripts/mpt.py \
  --long --duration 12 --script-file /caminho/roteiro.txt --aspect 16:9

# 4. Planejamento em duas etapas (gerar capítulos/outline primeiro):
~/.hermes/skills/media/moneyprinterturbo/scripts/mpt.py \
  --long --duration 15 --subject "História dos Sistemas Operacionais" --stop-at script
```

---

## 🧠 Alinhamento Semântico de Clipes (padrão de produção)

`--semantic-matching` vem **ligado por padrão** (`enable_semantic_matching=True`). Não passe `--no-semantic-matching` nos Shorts nem nos Longos do canal, salvo contingência explícita.

Fluxo automático:
1. Divide o roteiro em cenas com timestamps da legenda (Whisper ou SRT do Edge TTS).
2. Gera prompts visuais contextuais por cena, com filtro anti-anacronismo (nada de estoque moderno em pauta histórica).
3. Baixa clipes por cena e persiste `scene_materials_manifest.json` + `semantic_plan.json`.
4. Renderiza por timeline de slots 1:1 com a narração, sem drift acumulado.

Desligar: `--no-semantic-matching` (pipeline legado de cortes fixos).

---

## 🎬 Modo Vídeos Longos (`--long`)

Quando ativado `--long`:
- **Duração-alvo:** 3 a 35 minutos (`--duration <N>`, padrão 10 min). Limite técnico rígido: >35 min é rejeitado.
- **Roteiro em Capítulos:** Planejamento hierárquico com continuidade narrativa e termos de busca contextuais por capítulo.
- **Áudio & Legendas:** Síntese por blocos com retentativas independentes e alinhamento de SRT por offsets acumulados.
- **Normalização de Áudio:** Integrada nativamente para **−14 LUFS** e true peak ≤ **−1,5 dBFS** (pronto para YouTube, dispensando pós-processamento externo).
- **Aspecto Padrão:** `16:9` automático no modo longo (a menos que `--aspect 9:16` seja explicitamente passado).

---

## ⚙️ Opções e Parâmetros Principais

| Flag | Descrição | Padrão |
|---|---|---|
| `--subject`, `-s` | Tema do vídeo (o LLM gera roteiro e termos de busca) | — |
| `--script` | Roteiro pronto fornecido pelo usuário/agente | — |
| `--script-file` | Caminho para arquivo de texto contendo roteiro pronto | — |
| `--long` | Ativa o pipeline do modo vídeo longo (3 a 35 min) | Desativado (Shorts) |
| `--duration`, `-d` | Duração-alvo em minutos (3 a 35 min) | `10` (no modo longo) |
| `--chapters` | Número de capítulos (3 a 14, ou omita para automático) | Automático (~2.5 min/cap) |
| `--aspect`, `-a` | Proporção: `9:16` (Shorts), `16:9` (YouTube), `1:1` (Feed) | `9:16` (Short) / `16:9` (Long) |
| `--voice`, `-v` | Voz Edge-TTS (ex: `pt-BR-ThalitaMultilingualNeural-Female`, `pt-BR-AntonioNeural-Male`) | `pt-BR-ThalitaMultilingualNeural-Female` |
| `--language`, `-l` | Idioma do roteiro | `pt-BR` |
| `--source` | Origem dos vídeos: `pexels`, `pixabay`, `coverr`, `local` | `pexels` |
| `--materials` | Caminhos de vídeos/imagens locais para `--source local` | — |
| `--bgm-type` | Música de fundo: `random`, `none`, `custom`, `sonilo` | `random` |
| `--bgm-volume` | Volume da trilha sonora (0.0 a 1.0) | `0.2` |
| `--clip-duration` | Duração de cada corte em segundos | `5` (Shorts) / `10` (Longos) |
| `--no-subtitle` | Desativa legendas embutidas | Ativadas |
| `--semantic-matching` / `--no-semantic-matching` | Alinha clipes às cenas e beats da narração | **Ligado** |
| `--stop-at` | Interrompe em: `script`, `terms`, `audio`, `subtitle`, `materials`, `video` | `video` |

---

## 📦 Saídas e Arquivos Gerados

Os arquivos gerados são salvos em:
`/home/acer/Projetos/MoneyPrinterTurbo/storage/tasks/<task_id>/`

- `final-1.mp4`: Vídeo completo final com áudio normalizado (−14 LUFS), legendas e cortes prontos.
- `audio.mp3`: Faixa de narração TTS gerada.
- `subtitle.srt`: Legenda temporizada gerada pelo Edge-TTS ou Whisper.
- `script.json`: Roteiro, termos, metadados dos capítulos e fontes de materiais.
- `semantic_plan.json`: Cenas com timestamps e prompts visuais.
- `scene_materials_manifest.json`: Clipe por cena (gerado a partir de `--stop-at materials`).

Para entregar o vídeo no chat (Discord/WhatsApp):
Inclua `MEDIA:/home/acer/Projetos/MoneyPrinterTurbo/storage/tasks/<task_id>/final-1.mp4` na resposta final.

---

## ⚠️ Regras e Gotchas Importantes

1. **Tempo de Execução e Fila:** Geração de vídeos longos consome CPU e tempo (~25 min para 5 min de vídeo). Dispare em background caso necessário ou configure timeout alto. Apenas 1 tarefa roda por vez (`max_concurrent_tasks=1`).
2. **Pós-processamento Desnecessário:** O pipeline do MPT longo já aplica `-14 LUFS` e `+faststart`. **Não use scripts externos de tratamento (ex: `tratar-notebooklm-video.py`)** em vídeos gerados pelo modo longo.
3. **Créditos de Estoque:** Ao publicar no YouTube, copie os créditos de materiais listados em `script.json` para a descrição do vídeo.
4. **Alinhamento semântico é o padrão de produção:** não passe `--no-semantic-matching` nos vídeos do canal. O manifesto por cena fica em `scene_materials_manifest.json`.
