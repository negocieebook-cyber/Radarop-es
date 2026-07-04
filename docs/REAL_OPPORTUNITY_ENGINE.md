# Opportunity Engine Real Experimental

## Objetivo

O motor cruza snapshots reais de mercado da brapi, Healthbox calculado sobre esses snapshots e cadeias reais de opções EOD. Seu resultado é uma triagem de estudo (`estudar`, `atenção`, `evitar` ou `inconclusivo`), nunca uma recomendação ou ordem.

O motor principal MOCK / EXEMPLO permanece separado e não fornece dados para este módulo.

## EOD não é tempo real

As opções representam o arquivo de fim de pregão. Mesmo quando bid e ask permitem calcular `mid`, a informação pode estar defasada para o próximo pregão. Toda candidata carrega o aviso **Preço indicativo EOD; não usar como ordem a mercado**.

A prioridade de preço é: `mid` quando bid e ask existem, depois `close_eod`, depois `average_eod`. Sem essas bases, o preço fica indisponível. Bid e ask ausentes nunca são inventados.

## Estratégias permitidas

Somente estruturas de risco definido são pareadas:

- trava de alta com call;
- trava de baixa com put;
- venda de put travada;
- venda de call travada.

Venda descoberta, compra seca e venda coberta não são geradas nesta etapa. Os pares usam o mesmo ativo, vencimento e fonte, com strikes diferentes e preço indicativo disponível. O limite é de 30 candidatas por ativo.

## Status

- `estudar`: matemática completa, liquidez aceitável, dados críticos presentes e Healthbox sem contradição;
- `atenção`: matemática completa, mas há preço close/average EOD, liquidez baixa, vencimento curto, spread ausente ou confirmação contextual incompleta;
- `evitar`: matemática incompleta, preço ausente, liquidez ilíquida, risco/retorno ruim ou Healthbox contrário;
- `inconclusivo`: snapshot ausente, mercado ausente, opções indisponíveis ou acesso negado.

O score só existe quando matemática e Healthbox possuem dados mínimos. Caso contrário fica `None`, com a indicação de que não foi calculado por falta de dados.

## Segurança e evolução

O módulo não conecta corretora, não envia ordens e não registra entrada confirmada. O botão **Acompanhar estudo** guarda apenas uma referência na sessão da dashboard.

Uma evolução para intraday exige fornecedor compatível, timestamps e qualidade validados, regras de execução e testes adicionais. Até lá, os resultados devem ser usados somente como estudo EOD.
