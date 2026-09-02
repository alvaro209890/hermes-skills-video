# Interface do video.cursar.space

Mapeamento observado no MoneyPrinterTurbo v1.3.5 em 2026-08-27.

## Entrada superior

- **Gerenciador de tarefas:** abre painel com abas Todas, Em processamento, Concluídas e Falharam.
- **Ajustes:** abre LLM, APIs de materiais, interface, cache, presets e backup de chaves.
- **Language / 语言:** seleção de idioma; está em Português.

## Configurações do roteiro

| Controle | Efeito |
|---|---|
| Tema do vídeo | briefing usado para geração do roteiro |
| Idioma do roteiro | auto ou idioma explícito |
| Configurações avançadas | parágrafos, requisito adicional e prompt de sistema |
| Gerar roteiro e palavras-chave | chama o LLM e preenche os dois campos |
| Roteiro do vídeo | roteiro próprio; quando preenchido, dispensa geração de roteiro |
| Gerar palavras-chave | cria consultas de mídia a partir do roteiro |
| Palavras-chave | consultas em inglês, separadas por vírgula |

## Vídeo

| Controle | Opções principais / observação |
|---|---|
| Fonte | Pexels, Pixabay, Coverr, arquivo local e integrações generativas configuradas |
| Concatenação | aleatória ou sequencial |
| Ajustar à ordem do roteiro | gera mais termos em ordem narrativa e concatena na mesma ordem |
| Transição | nenhuma, aleatória, fade, slide e, na WebUI, zoom |
| Proporção | 9:16 e 16:9; o modelo também suporta 1:1 |
| Duração máxima por clipe | não controla a duração total |
| Velocidade do clipe | altera só o visual, de 0,5× a 2× |
| Vídeos por execução | cria múltiplas variações |
| Codificador | padrão/libx264 ou hardware com fallback |

## Áudio

- Modo: Automática, Enviar ou Nenhuma.
- Edge TTS aparece como **Azure TTS V1** e não exige chave.
- Voz portuguesa validada: `pt-BR-ThalitaMultilingualNeural-Female`.
- Ajustes: volume, velocidade, amostra curta e prévia completa.
- BGM: nenhuma, aleatória, arquivo próprio, Sonilo ou ElevenLabs conforme configuração.

## Legendas

- Liga/desliga; fonte; posição superior/central/inferior/personalizada;
- cor, tamanho, contorno, espessura;
- fundo, cor do fundo e fundo arredondado.

## Geração

O botão final é **Começar a Gerar Vídeo**. A WebUI submete uma tarefa em background, com
concorrência máxima de 1. O painel atualiza via fragmentos Streamlit, sem apagar os campos.

## Gerenciador de tarefas

Cada linha mostra status, atualização, tema, progresso e ações:

1. Reproduzir — no servidor headless, abre player embutido;
2. Baixar — entrega o `final-*.mp4`;
3. Abrir pasta — no servidor mostra o caminho relativo;
4. Gerar novamente — restaura roteiro e parâmetros, mas exige novo clique para gerar;
5. Excluir — indisponível enquanto geração ou publicação estiver ativa.

Histórico é reconstruído de `storage/tasks/*/script.json` e `final-*.mp4`, portanto sobrevive
a reinício do Streamlit.

## Ajustes

- **LLM:** provider, chave, base URL, modelo e teste de conexão.
- **Materiais:** chaves Pexels/Pixabay/Coverr e fontes pagas.
- **Interface:** preferências e publicação automática.
- **Presets:** exporta/importa ajustes de roteiro, vídeo, áudio e legenda, sem uploads.
- **Backup de chaves:** arquivo em texto simples; nunca baixar ou expor por iniciativa própria.
- **Cache:** estatísticas e limpeza por idade; não limpar durante geração.

## Segurança operacional

- O site está público via Cloudflare; não trate como painel privado.
- Não exiba chaves, tokens ou backup de credenciais.
- Não use Excluir, limpeza de cache ou publicação automática sem ordem específica.
- Provedores WaveSpeed, LoomLoom, Sonilo e ElevenLabs podem cobrar; exigir confirmação explícita.
