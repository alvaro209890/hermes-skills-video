# Protocolo de conversa no WhatsApp — compartilhado pelas 3 skills de vídeo

> Fonte: `~/Documentos/Planejamento_Skills_Video/PLANO_HERMES.md` §0 e §2.
> Este arquivo é o resumo operacional. **O protocolo não pode divergir entre as skills.**

O canal é o WhatsApp, e isso desenha a skill. Não existe imprimir 400 linhas, abrir preview
ou esperar `Ctrl+C`. Existe: mensagem curta (corte em **4.096 caracteres**), anexo nativo,
e o Álvaro saindo do chat e voltando 40 minutos depois.

**A skill é, antes de tudo, um protocolo de conversa. O `ffmpeg` é a parte fácil.**

## 1. Entradas aceitas

| O Álvaro manda | Como chega | O que fazer |
|---|---|---|
| **Link** | texto | detecta URL → confirma intenção → dispara |
| **Vídeo** (arquivo) | caminho absoluto em `~/.hermes/cache/videos/` | **pula o download inteiro** |
| **Print / imagem** | `~/.hermes/cache/images/` | `vision_analyze` → referência visual |
| **Áudio / nota de voz** | ⚠️ chega **já transcrito** (STT local, modelo `base`) | pedido falado. Para usar como referência de **timbre**, pegar o `.ogg` em `~/.hermes/audio_cache/` pelo `terminal` — o texto não basta |
| **Documento** (`.md`, `.txt`) | inline até 100 KB | roteiro pronto → pula para produção |
| **Texto** | mensagem | briefing, ajuste, resposta |

**Regra de disparo:** link solto **não** dispara o pipeline. Responder curto e perguntar.
Exceção: a mensagem já traz a intenção — *"analisa esse"*, *"faz um igual"*, *"dubla pra inglês"*.

**Debounce de 5 s** (10 s para fragmentos longos): o adaptador junta mensagens em rajada numa
única chamada. Então *link* + *"faz um igual"* mandados separados **chegam juntos** —
**não responder duas vezes** ao que é uma ordem só.

## 2. Saídas

| Entrega | Forma | Quando |
|---|---|---|
| **Aceite** | texto ≤2 linhas | em segundos, **sempre** |
| **Progresso** | texto curto por marco | jobs acima de ~2 min |
| **Pergunta** | `clarify` (lista numerada) | nos pontos ⏸️ |
| **Resumo** | texto **≤8 linhas** | ao terminar |
| **`ANALISE.md`** | `[[as_document]] MEDIA:/caminho/ANALISE.md` | junto do resumo |
| **Keyframes** | `MEDIA:` (imagem) | 2–3 que sustentam o veredito |
| **Vídeo final** | `MEDIA:/…/final_9x16.mp4` + legenda | toca dentro do chat |
| **Arquivo grande** | link (tunnel / `cursar.space`) | acima de ~16 MB |

**O chat não é lugar de relatório.** O resumo cabe numa tela de celular; o `.md` é o artefato.
Relatório longo no chat vira 6 mensagens picotadas e ninguém lê.

## 3. ⏸️ Perguntar e aguardar — tool `clarify`

- Até **4 opções** + a 5ª automática "Outro" (resposta livre);
- viram **lista numerada** — o Álvaro responde "2";
- sem `choices` → pergunta aberta;
- **nunca** enumerar as opções dentro do texto da pergunta (renderiza duplicado);
- **timeout: 1.800 s (30 min)** (`agent.clarify_timeout`).

**Orçamento: no máximo 3 perguntas por vídeo.** O resto é **default declarado** — anunciar e
seguir: *"vou de 9:16, 30 s, voz Francisca, estilo jjk-dark — só falar se quiser diferente."*
Perguntar demais é pior que errar o preset; o Álvaro está no celular.

### Onde perguntar

| ⏸️ Momento | Pergunta | `choices` |
|---|---|---|
| Antes de gastar | "Analiso esse Reel? Uns 4 min." | `["Analisa","Só o roteiro","Depois"]` |
| Estilo | "Qual estilo?" | `["Igual ao @silv.mind","Igual ao RM RAPS","Outro que eu já analisei"]` |
| Duração | "Quanto tempo?" | `["15s","30s","45s","Sem limite"]` |
| Voz | "Qual voz?" | `["Francisca (padrão)","Antônio (masc.)","Mais séria","Mais irônica"]` |
| Idioma | "Pra qual idioma?" | `["Inglês","Espanhol","Os dois","Outro"]` |
| Custo/tempo | "Usa API paga (~US$ X), ~Y min. Sigo?" | `["Segue","Faz a versão barata","Cancela"]` |
| Roteiro | "Roteiro pronto. Renderizo?" | `["Renderiza","Encurta","Refaz o gancho"]` |
| Trocadilho | "'Você Que Sabe' não tem equivalente. Qual caminho?" | `["Adaptação livre","Mantém em pt","Legenda explicando"]` |

**Se o timeout de 30 min estourar:** não adivinhar e não cancelar em silêncio. Gravar o estado
no `kanban.db`, mandar *"fiquei sem resposta; parei em `<etapa>`, é só falar 'continua'"*, e
encerrar o turno. Retomada por `session_search`/`memory`.

**Aprovação de texto antes do render** é a regra que mais economiza: texto é barato de revisar.

## 4. Job longo — progresso sem travar o chat

1. Trabalho pesado roda como **processo em background** (`terminal`), **não** como sequência de
   tool calls. Limites: `max_turns: 150`, `gateway_timeout: 3600 s`, aviso em `1200 s`.
2. O script avisa sozinho a cada marco, por CLI — funciona **fora** do turno do agente:
   ```
   hermes send --to whatsapp "🎬 transcrito (2:14 de áudio) — vendo os frames agora"
   ```
3. Marcos padrão (não mais que estes — notificação demais vira spam):
   `baixado` → `transcrito` → `vi os frames` → `roteiro pronto` (⏸️) → `renderizando` → `pronto`.
4. O job entra no `kanban.db` com slug e chat de origem, e responde a *"como tá aquele vídeo?"*.
5. O WhatsApp **já mostra em tempo real qual ferramenta está rodando** — não é preciso narrar
   cada passo por texto.

## 5. Gotchas do canal (PLANO_HERMES §5)

- **Heredoc dispara aprovação** (janela de 60 s) — inviável pelo celular. Scripts vão como
  **arquivo** em `scripts/`; trecho pesado por `delegation` (`subagent_auto_approve: true`).
- **STT do chat é o modelo `base`** — nota de voz técnica transcreve mal. Repetir o entendimento
  em uma linha antes de gastar.
- **Chunking em 4.096 caracteres** — resumo ≤8 linhas, o `.md` como documento.
- **Anexo confortável até ~16 MB**; acima, link. `[[as_document]]` evita a recompressão do WhatsApp.
- **`allowed_chats` restrito ao número do Álvaro** — atenção ao testar de outro número.
- **Cron roda sem contexto do chat** e com `approvals.cron_mode: deny` — job agendado precisa ser
  autossuficiente e **não pode depender de `clarify`**.
- **`delegation`:** paralelismo real é **3** (`max_concurrent_children`), não N.
