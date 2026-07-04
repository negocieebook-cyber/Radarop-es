# Conditional Entry Engine

## Objetivo

O Conditional Entry Engine transforma candidatas reais EOD em planos condicionais para validação no pregão seguinte. Ele mostra preço de referência, limite aceitável, confirmações e invalidações, sem indicar entrada imediata e sem enviar ordens.

## Preço EOD versus preço executável

Preço EOD é uma fotografia de fim de pregão. Mesmo quando existe `mid`, ele não representa garantia de execução na abertura seguinte. Toda estrutura mostra: **Entrada condicional para validar no pregão. Preço EOD não é executável.**

Campos ausentes permanecem indisponíveis; o motor não inventa bid, ask, preço, liquidez ou contexto gráfico.

## Limites de preço

Para travas de débito, o risco/retorno mínimo desejado é 1,2:

`débito máximo = largura / (1 + 1,2)`

Para travas de crédito:

`crédito mínimo = 20% da largura`

Esses limites são filtros iniciais de estudo, não preços de ordem.

## Status

- `entrada_condicional`: matemática completa, faixa de preço aceitável, liquidez adequada, Healthbox sem contradição e vencimento observável;
- `acompanhar_na_abertura`: estrutura calculável, mas preço um pouco caro, base close/average, liquidez intermediária, spread ausente ou contexto em atenção;
- `evitar`: matemática incompleta, crédito baixo, débito excessivo, Healthbox contrário, liquidez ilíquida ou vencimento curto demais;
- `inconclusivo`: snapshots, preços ou dados críticos insuficientes.

## Confirmação e invalidação

As confirmações exigem preço atual no pregão, liquidez, spread, suporte/resistência, tendência e respeito ao limite de débito ou crédito. As invalidações cobrem rompimento contra a tese, custo fora da faixa, crédito insuficiente, spread aberto, liquidez ruim, dados desatualizados e ausência de preço atual.

## Limites e evolução

O engine usa opções EOD e não substitui dados intraday. Antes de qualquer evolução operacional são necessários Bulkowski real, melhores métricas de liquidez, cobertura de mais ativos e avaliação de um fornecedor intraday. Nenhuma integração com corretora existe nesta etapa.
