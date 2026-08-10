# Sincronia na dublagem — a cascata

> Fonte: `README.md` §8 · `PLANO_HERMES.md` §3.3 passos 5–7 e §3.5.
> **Meta: desvio ≤150 ms por segmento**, relatado numericamente no chat.

## O problema

**Português é ~15–30 % mais longo que inglês.** Traduzir e sintetizar sem restrição produz
narração que atropela a cena. A sincronia se resolve em camadas, **nesta ordem** — cada uma só
entra se a anterior não bastou.

## A cascata

| # | Camada | Como | Limite |
|---|---|---|---|
| 1 | **Tradução com restrição de comprimento** | o LLM (`deepseek-v4-pro`) recebe o nº de caracteres/sílabas alvo por segmento e devolve **3 variantes** (curta / média / longa) | é a camada mais barata — usar sempre |
| 2 | **Absorção no silêncio** adjacente | encaixar o excedente nas pausas entre falas | só onde há silêncio real |
| 3 | **Time-stretch preservando pitch/formante** | filtro `rubberband` do FFmpeg | **±10 %**, nunca mais — passa disso e a voz soa robótica |
| 4 | **Nova tradução mais curta** | volta ao passo 1 com orçamento menor | |
| 5 | **Marcar para revisão** | entra no relatório de QA como pior caso | não esconder |

## Segmentação

Segmentar por **unidade de fala** (pausa > 200 ms), **não** por frase gramatical. Frase
gramatical ignora onde a pessoa respira — e é a respiração que define o encaixe.

## QA numérico (o que vai no chat)

```
pronto — desvio médio 90 ms, p95 160 ms, pior 210 ms em [00:14]
```

Sempre: **média, p95 e pior caso com o timestamp**. O Hermes **não ouve** o resultado — o QA é
numérico e a aprovação final é humana.

## Comando executável

O filtro do FFmpeg basta; não exigir por engano o binário `rubberband` separado:

```bash
scripts/encaixar-fala.sh fala_pt.wav fala_pt_fit.wav 2.850 0
```

Equivalente central:

```bash
ffmpeg -i fala.wav -af \
  "aresample=48000,rubberband=tempo=1.06:pitch=1:formant=preserved:pitchq=quality,apad,atrim=0:2.850" \
  -ar 48000 -c:a pcm_s24le fala_fit.wav
```

Se `duração_entrada / slot` sair de `0.90–1.10`, o script retorna código 3 e manda
reescrever/ressintetizar. Não force um número maior só para “fechar”.

## O que preservar

- **A trilha original.** `Demucs` (`htdemucs`) separa `vocals.wav` + `music.wav`; a narração nova
  entra por cima da `music.wav` original, com ducking. Nunca remontar a trilha do zero.
- **As legendas saem do áudio dublado REAL**, não da tradução em texto — o TTS muda a duração.

## Limites conhecidos

- **Demucs em CPU compartilhada: ~5–10× tempo real.** Clipe de 4 min derruba a responsividade do
  Hermes. **Avisar o tempo estimado antes** e, se possível, agendar fora do horário de uso.
- **Sem lip-sync.** Irrelevante em narração off e anime edit; **bloqueante em talking head de
  close** — avisar, não entregar calado.
- **Prosódia:** TTS não faz ironia. O tom das referências *é* irônico.
- **Licenças:** XTTS-v2 é CPML (proíbe uso comercial); voz clonada de pessoa real exige
  autorização. Gravar motor e licença na saída.
