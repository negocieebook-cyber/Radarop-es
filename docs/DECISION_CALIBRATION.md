# Calibração de Decisão

## Hard blocker versus soft warning

Um **hard blocker** impede entrada condicional: matemática incompleta, preço ou strikes ausentes, liquidez ilíquida, largura inválida, risco/retorno impossível, snapshot ausente, acesso negado ou vencimento fora da faixa segura.

Um **soft warning** exige confirmação, mas não invalida sozinho a estrutura: preço close/average EOD, Healthbox neutro, liquidez baixa ou média, rVol baixo, RSI neutro, custo ligeiramente acima, crédito ligeiramente abaixo ou spread ainda não confirmado.

Healthbox `não confirma` só bloqueia quando o contexto contradiz diretamente a direção da estrutura. Tendência lateral ou leitura neutra conduz a **acompanhar na abertura**.

## Por que acompanhar na abertura

Dados EOD não representam preço executável. A categoria permite preparar uma lista de observação sem fingir que preço, spread ou liquidez continuarão iguais no pregão seguinte. A mensagem operacional permanece: confirmar preço, spread e negócios antes de considerar o estudo.

## Tolerâncias controladas

Para débito:

- débito máximo: `largura / (1 + 1,2)`;
- limite para acompanhar: `débito máximo × 1,15`;
- acima desse limite: evitar.

Para crédito:

- crédito mínimo: `20% da largura`;
- limite para acompanhar: `crédito mínimo × 0,85`;
- abaixo desse limite: evitar.

As tolerâncias não eliminam perda máxima, ganho máximo, break-even, preço ou liquidez como requisitos obrigatórios.

## Segurança

Nenhum dado ausente é inventado. Preço EOD não é ordem nem garantia de execução. O sistema não conecta corretora, não envia ordens e mantém o motor mockado separado. Uma entrada condicional é somente um plano para validação posterior.
