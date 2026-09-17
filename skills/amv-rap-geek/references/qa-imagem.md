# QA de imagem: métricas, persistência e prova visual

Use esta referência ao alterar `ferramentas/imagem.py` ou interpretar uma reprovação de
`estudio.py imagem` / `estudio.py qa`.

## Página de mangá: persistência antes de reprovar *(Naruto, 15/09/2026)*

O classificador amostra a 6 fps e marca como candidato o quadro com mais de 55% de pixels
claros e sem saturação. Isso é só um **indício por quadro**: céu, neve, flash e fundo branco
do próprio anime também podem cruzar o limiar.

🔴 **Nunca some amostras isoladas como se fossem uma página contínua.** O portão usa
`pagina_s` apenas para corridas contíguas de pelo menos 0,5 s. A soma bruta continua em
`pagina_candidata_s`, para calibração. Se a mensagem não consegue apontar o início de um
intervalo sustentado, ela não pode reprovar o master.

No Naruto, quatro amostras espalhadas da Konan em fundo claro totalizavam 0,67 s, mas não
formavam bloco. A regra antiga reprovava e imprimia os dois-pontos sem nenhum tempo depois.
A correção passou em `ferramentas/provar_imagem.py` (3/3) e no master real com
`python3 ferramentas/estudio.py qa naruto`.

Mesmo quando o bloco é sustentado, abra o instante na folha: o número encontra suspeitos;
quem distingue página parada de arte canônica clara é a inspeção visual.

## Regressão obrigatória

```bash
python3 -m py_compile ferramentas/imagem.py ferramentas/provar_imagem.py
python3 ferramentas/provar_imagem.py
python3 ferramentas/estudio.py qa <slug-real>
```

As três provas sintéticas cobrem candidatos isolados, uma corrida sustentada de 0,67 s e o
limiar exato de 0,50 s. O projeto real confirma decodificação, integração com o manifesto,
relatório e decisão final do portão.
