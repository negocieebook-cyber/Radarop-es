# Estratégias de Opções

As fórmulas abaixo são conceituais e devem ser recalculadas por contrato, multiplicador e custos. Sem preços completos, o sistema deve mostrar “não calculado por falta de dados”.

| Estratégia | Quando usar | Quando evitar | Ganho máximo | Perda máxima | Break-even no vencimento | Risco principal |
|---|---|---|---|---|---|---|
| Compra de call | alta forte esperada | volatilidade/prêmio excessivos ou tese lateral | ilimitado menos prêmio | prêmio pago | strike + prêmio | perda do prêmio e theta |
| Compra de put | queda forte ou proteção | prêmio excessivo ou baixa volatilidade esperada | strike menos prêmio, limitado a ativo zero | prêmio pago | strike − prêmio | perda do prêmio e theta |
| Venda coberta de call | lateralidade/alta moderada com ações em carteira | alta explosiva ou intenção de manter ações sem venda | prêmio + valorização até strike | queda da ação menos prêmio | custo da ação − prêmio | queda do ativo e alta limitada |
| Venda de put com caixa | desejo de comprar abaixo do mercado | queda acentuada ou caixa insuficiente | prêmio recebido | strike − prêmio, se ativo for a zero | strike − prêmio | forte queda e exercício |
| Trava de alta com call | alta moderada | movimento lateral/queda ou débito caro | largura dos strikes − débito | débito pago | strike comprado + débito | perda do débito |
| Trava de baixa com put | queda moderada | alta/lateralidade ou débito caro | largura dos strikes − débito | débito pago | strike comprado − débito | perda do débito |
| Venda de put travada | alta/lateralidade com suporte | risco de queda/volatilidade crescente | crédito recebido | largura dos strikes − crédito | strike vendido − crédito | queda abaixo da proteção |
| Venda de call travada | baixa/lateralidade com resistência | risco de alta/volatilidade crescente | crédito recebido | largura dos strikes − crédito | strike vendido + crédito | alta acima da proteção |
| Collar | proteger ações limitando custo | expectativa de alta forte sem aceitar teto | limitado pelo strike da call | limitado pela put, ajustado por prêmios | custo líquido ajustado | alta limitada e risco residual |
| Protective put | proteger carteira mantendo alta aberta | put muito cara | alta da ação menos prêmio | queda até strike da put + prêmio | custo da ação + prêmio | custo recorrente da proteção |
| Iron condor | lateralidade e volatilidade implícita alta | tendência forte ou evento binário | crédito recebido | maior largura das asas − crédito | dois pontos: strikes vendidos ± crédito | rompimento de uma das asas |
| Calendar | preço perto do strike e diferença temporal favorável | movimento brusco ou curva desfavorável | variável, não fixo antes do vencimento curto | débito pago | variável | volatilidade e passagem desigual do tempo |
| Diagonal | direção moderada com diferença de strikes/prazos | movimento fora da faixa ou estrutura cara | variável | geralmente débito, sujeito à montagem | variável | preço, volatilidade e exercício antecipado |

Nenhuma estratégia deve ser exibida como oportunidade sem liquidez, perda máxima e fontes críticas válidas.
