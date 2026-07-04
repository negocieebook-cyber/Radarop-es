# Opportunity Engine

O motor simula o futuro funil de oportunidades usando apenas universo, cadeia e snapshots **MOCK / EXEMPLO**. Ele carrega ativos, verifica elegibilidade, pareia pernas de mesmo vencimento, calcula risco, aplica liquidez/spread, Healthbox, Bulkowski, checklist e score, e explica cada decisão.

Estratégias permitidas nesta etapa: trava de alta com call, trava de baixa com put, venda de put travada, venda de call travada e venda coberta. Venda descoberta e qualquer estrutura sem perda máxima conhecida são proibidas.

Uma oportunidade só é aprovada com cálculo completo, liquidez mínima, spread aceitável, score calculado e Healthbox não contrário. Alertas de liquidez média, spread médio, vencimento curto ou Bulkowski inconclusivo levam a atenção. Falta crítica, liquidez/spread ruim, risco/retorno insuficiente ou contexto contrário levam a reprovação ou score não calculado.

Prêmio alto isolado nunca aprova uma operação. Campos ausentes permanecem ausentes; nenhuma estatística ou cotação é inventada.
