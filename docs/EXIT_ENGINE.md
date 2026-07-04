# Position Monitor / Exit Engine

## Objetivo

O motor transforma dados disponíveis de uma posição e do contexto atual em alertas explicáveis. Ele não encerra posições, não envia ordens e não se conecta a corretora. **Alerta é informação; ordem é uma ação externa que este projeto não executa.**

## Entradas

São necessários, conforme a regra: preço real de entrada, quantidade, marcação atual da estrutura, ganho/perda máximos por unidade, dias até vencimento, strikes, preço do ativo, suporte/resistência, leitura Healthbox e leitura Bulkowski. Nesta etapa, tudo é MOCK / EXEMPLO.

## Regras

- P/L: marcação menos entrada, por unidade e multiplicado pela quantidade.
- Captura: lucro por unidade dividido pelo ganho máximo por unidade.
- 50%–75% de captura: realizar parcial; 75% ou mais: realizar total.
- Até 10 dias: atenção/vencimento próximo; até 5 dias sem evolução: sair agora.
- Suporte perdido em tese altista ou resistência rompida contra tese baixista: tese invalidada.
- Healthbox sem confirmação, Bulkowski inconclusivo e proximidade de strike/níveis geram atenção.
- Limite de perda atingido gera sair agora.

## Status

`manter`, `atenção`, `realizar parcial`, `realizar total`, `ajustar`, `sair agora`, `tese invalidada`, `vencimento próximo` ou `inconclusivo por falta de dados`. Cada resultado inclui severidade, motivo, detalhes, tipo e fonte.

## Falta de dados

O motor pode e deve dizer “não sei avaliar por falta de dados”. Marcação, níveis ou estratégia ausentes nunca são estimados silenciosamente. Essa recusa protege o usuário de um alerta com falsa precisão.
