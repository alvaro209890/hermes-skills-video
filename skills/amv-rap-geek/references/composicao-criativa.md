# Composição criativa por trecho

Decisão do Álvaro, 12/09/2026: as referências são inspiração de linguagem visual.
A IA inventa combinações de acordo com o personagem, a letra e o momento musical.
Não reproduzir o quadro do Choso nem transformar frequência de efeitos, cor ou fps
de uma referência em obrigação para todo AMV.

## Referências e interpretação

Referências locais no Acer, em `Video_Studio/refs/rmraps/`: Choso
(`choso_rmraps.mp4`, `gLbTrypXJPg`), Tengen (`tengen_rmraps.mp4`, `jhjNpTzuLtE`)
e o último link enviado pelo Álvaro (`higuruma_rmraps.mp4`, `-g1DBUybMBY`).
O terceiro arquivo foi confirmado em 1920x1080, 60 fps. Isso não determina a taxa
do projeto; mantenha o fps escolhido consistente até a exportação.

Use as referências para observar contraste entre pausa e impacto, hierarquia da
tipografia, painéis, textura e relação entre palavra e gesto. Cada decisão precisa
de motivo ligado à cena e ao verso atual. A leitura do personagem e da letra vale
mais que uma meta numérica de estilo.

## Ferramentas e fluxo

`ferramentas/estudio.py compor entrada.json --saida propostas.json` propõe receitas.
É uma heurística local de vocabulário, **não uma chamada de modelo nem entendimento
de canon**. Revise metáforas, negação, nomes próprios e significados ambíguos.
O campo `motivo` deve explicar a decisão criativa da IA; substitua a justificativa
automática quando ela não sustentar o plano.

`ferramentas/estudio.py render-composicao propostas.json --indice 0 --saida peca.mp4`
renderiza **uma peça silenciosa**, padrão 1920x1080, 30 fps, acompanhada de JSON com
tempo da fonte e quantidade de quadros. `--fps 60` está disponível quando o projeto
pedir. Caminhos relativos de `fonte` são relativos ao JSON.

`ferramentas/estudio.py montar-composicao propostas.json --saida montagem.mp4`
monta todas as peças do JSON com o motor de transições A→B (`ferramentas/montagem.py`).
A linha do tempo e a duração total permanecem rigorosamente intactas: as transições
operam exclusivamente substituindo quadros ao redor do corte (`inicio_planos`), sem
adiantar nem atrasar o beat ou o arquivo de legendas `.ass`.

Transições disponíveis (29 no catálogo):
- Cortes e continuidade: `corte`, `match` (continuidade de pose)
- Dissoluções: `diss`, `dissl` (varredura esquerda), `dissr` (varredura direita), `dissw` (flash branco tênue), `dissb` (blur dinâmico)
- Geométricas e radiais: `circulo`, `radial`, `lamina_dir`, `lamina_esq`
- Dinâmicas e camera: `whip`, `whip_dir`, `whip_esq`, `whip_cima`, `whip_baixo`, `zoom`
- Impacto, sakuga e luz:
  - `impact_frame`: quadro sakuga binarizado em P&B com contraste extremo (std > 90) e microtremor de colisão
  - `impact_color`: o mesmo impact frame com explosão na cor da aura do personagem
  - `negativo`: flash negativo/invertido de 3 frames para golpes de espada / corte invisível
  - `rgb_split`: deslocamento cromático entre canais R e B no pico da transição
  - `flash`, `flashc` (aura ciano/colorida), `flashr` (vermelho), `dip` (fade escuro)
- Orgânicas e temáticas: `tinta` (sangue/veneno), `fumaca` (sombra), `energia` (fogo/raio), `painel` (zoom em quadrinho)

A escolha da transição em `composicao.escolher_transicao` considera continuidade de movimento
anotada (`whip_<direcao>`), pose correspondente (`match`), papel da cena (seção de respiro
como ponte/outro escolhe `diss`), família do personagem e proteção de alta luminosidade
(evita flash em cenas muito claras). As transições usam foco visual normalizado `[x, y]`.
As partículas suportam animação individualizada por sprite com rotação e fase (`particulas_animadas`).

## Vazio Declarado (Blackout Intencional)

A referência do RM RAPS usa frequentemente momentos de silêncio visual (telas escuras de 1 a 2 s
com somente a letra da música no centro da tela antes de um drop ou virada dramática).
Para que o porteiro de integridade (`imagem.py`) não reprove o master por "tela morta acidental",
declare os intervalos no manifesto `projeto.json` em `"vazios_declarados": [[inicio_s, fim_s], ...]`.
O validador ignora os blocos declarados e protege contra telas pretas acidentais de render.

## Entrada mínima

```json
{
  "familia": "sombra",
  "personagem": "Sung Jin-Woo",
  "aura": "#3AA0FF",
  "apoio": "#9B70DC",
  "semente": 12,
  "planos": [
    {"fonte": "fontes/cena_limpa.mp4", "de": 3.0, "dur": 1.2,
     "letra": "Ergam-se das sombras", "papel": "refrao"}
  ]
}
```

`dur` é a duração de **saída**, quantizada por `round(dur*fps)`.
As rampas calculam `dur_fonte = dur_saida*2/(k0+k1)`. Audite a janela calculada
contra legendas, marcas e limites reais da fonte; `ffprobe` sozinho não comprova
que o fim está livre de preto. Não mova a voz ou a legenda para acomodar o efeito.

Famílias disponíveis: `lamina`, `fogo`, `sangue`, `sombra`, `raio`, `veneno`,
`gelo`, `vento`, `luz`. São pontos de partida; a IA pode combinar primitivas de
outras famílias quando houver motivo narrativo. Personagem novo não exige script.

## Receita revisável

```json
{
  "movimento": "push",
  "tratamento": "duotone",
  "rampa": "impacto",
  "transicao": "corte",
  "camadas": [
    {"primitiva": "anel", "cor": "#3AA0FF", "entrada": "fecha",
     "de": 0.1, "dur": 0.45, "pico": 0.7, "semente": 12},
    {"primitiva": "particulas", "motivo_particula": "fumaca",
     "cor": "#9B70DC", "entrada": "abre", "dur": 1.2,
     "pico": 0.6, "parametros": {"n": 180}}
  ],
  "painel": {"larg_frac": 0.3, "giro": -6, "x": "W*0.08", "y": "H*0.25"},
  "cartela": "ERGAM-SE",
  "nome_vertical": "SUNG"
}
```

`camadas` aceita várias camadas na ordem de composição e prevalece sobre o campo
singular `camada` da proposta automática. `camadas: []` remove as camadas.
Painel, cartela e nome são opcionais. O painel usa a própria cena; para outra fonte
use `painel.fonte` absoluto e `painel.de`, com janela previamente auditada.

Primitivas: `mancha`, `risco`, `raios`, `estilhaco`, `anel`, `particulas`.
Motivos de partícula: `lasca`, `brasa`, `gota`, `fumaca`, `faisca`, `petala`,
`estilha`, `brilho`. Entradas: `abre`, `fecha`, `parado`; toda camada tem alpha
decrescente e termina em `de+dur`. Os parâmetros próprios da primitiva entram em
`parametros` (ex.: `n`, `lados`, `forca`, `raio_livre`).

Tratamentos: `nenhum`, `manga`, `duotone`, `quente`, `frio`. O duotone usa a aura
do plano. A tipografia de cartela usa Rubik Distressed; a legenda continua Cinzel.

## Escolha e verificação

- Parta da cena canônica e do verso revisado. Use efeito para enfatizar uma ideia,
  revelar algo ou organizar a tela; preserve também trechos de respiro.
- Propostas automáticas limitam camadas a 35% dos planos, repetição da mesma
  primitiva a cinco planos e transições de impacto a intervalos de 3,6 s (whip: 7 s).
  São proteções iniciais, não substitutos para a composição da IA.
- Composição nova cabe nos módulos `camadas.py` e `composicao.py`; amplie-os quando
  precisar de outra primitiva. Não copie um render por personagem.
- Olhe início, pico, meio e saída no vídeo codificado. PNG isolado não comprova
  animação. Confira rostos, leitura do texto, transparência e moldura do painel.
- Regressões: `python3 ferramentas/provar_composicao.py` e `provar_efeitos.py`.
  Antes de entregar o AMV completo, mantenha os portões de sincronia, imagem, texto
  e transição, além da inspeção visual e sonora do master final.

Implementação e validação: Codex, 12/09/2026, retomando a sessão Claude
`cc0e2420-046e-458d-b051-ef3655019da1`.

## Rampa `lenta` *(Doma, 14/09/2026)*

`efeitos.RAMPA["lenta"] = (1.70, 1.70)`: câmera lenta constante. Serve quando o plano de câmera
limpo da fonte é **mais curto que o verso** e a borda cairia num corte interno da fonte
(SKILL §4h-bis). A janela de fonte vira `dur / 1,7`; no validador do projeto,
`RAMPA_K["lenta"] = 3,40` (a soma k0 + k1). Usada nos planos da Kotoha, cujos planos de câmera
têm ~1 s.
