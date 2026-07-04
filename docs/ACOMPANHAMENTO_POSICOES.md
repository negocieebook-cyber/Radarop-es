# Acompanhamento de Posições

## Ações da oportunidade

- **Entrei nessa posição:** cria uma posição aberta após confirmação dos dados reais da execução.
- **Não entrei:** registra a decisão sem criar posição.
- **Acompanhar sem entrar:** cria observação da tese e dos gatilhos.
- **Descartar:** encerra a oportunidade com motivo registrado.

## Dados salvos ao entrar

Ativo, estratégia, pernas e quantidades, preços executados, custos, data/hora, vencimento, tese, fonte, perda/ganho máximos, break-even, alvo, stop/invalidação e observações. Preço sugerido nunca substitui preço executado.

## Status e saídas

Estados previstos: observando, aberta, atenção, realizar parcial, sair, encerrada e expirada. Regras de saída devem ser objetivas, como percentual do ganho máximo, perda da tese/suporte, proximidade do vencimento, liquidez ou evento relevante. Alertas apoiam a decisão; não enviam ordens.

## Histórico

Toda alteração deve gerar registro com data/hora, motivo e origem. A versão atual persiste decisões demonstrativas localmente em `data/positions.json` e `data/history.json`; todos esses registros são **MOCK / EXEMPLO**, podem ser limpos pela interface e não representam posições em corretora.
