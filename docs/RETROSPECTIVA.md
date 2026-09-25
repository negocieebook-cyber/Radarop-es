# Retrospectiva das candidatas vencidas

## Objetivo

Fechar o ciclo da rotina: candidatas salvas na Watchlist de Abertura cujo vencimento já passou são avaliadas com o fechamento EOD do ativo, mostrando o que teria acontecido com a tese. É aprendizado de rotina, não registro de execução.

## Como funciona (`app/retrospective_engine.py`)

1. **Preço do vencimento**: histórico diário gratuito do opcoes.net.br (`QuotesHistoryByAsset`, cache local de 6 horas). Usa o fechamento do pregão do próprio vencimento ou, se aquele dia não tiver candle, o último pregão anterior em até 10 dias.
2. **Entrada**: se a candidata foi convertida em posição com `preco_real_entrada`, o cálculo usa esse preço real. Caso contrário, usa a `preco_eod_referencia` da candidata e o resultado é rotulado como estimativa ("entrada real não registrada"). Candidatas invalidadas sem conversão ficam **inconclusivas** — a saída real não foi registrada no app.
3. **Payoff por estrutura** (por contrato): call debit spread e put debit spread (`intrínseco − entrada`), bull put spread e bear call spread (`entrada − perda`), long call/put (`intrínseco − entrada`) e covered_call (`entrada − intrínseco`). Estrutura não suportada ou campo ausente produz resultado inconclusivo com a lista de campos faltantes — nada é inventado.

## Resumo por estratégia

A página **Retrospectiva** (grupo Acompanhamento) mostra o resumo agregado: quantas vencidas foram avaliadas, ganhos/perdas/zerados estimados, taxa de ganho e soma do P/L estimado por tipo de estrutura. Cada linha mostra ativo, estratégia, strikes, vencimento, preço do ativo na data do vencimento (com a data usada), entrada e fonte da entrada.

## Limites honestos

O resultado é `DADOS REAIS EOD / ESTIMATIVA`: usa preço real do vencimento, mas presume realização no vencimento, sem custos, sem saída antecipada e sem confirmação de execução. Candidatas ainda ativas aparecem como "aguardando avaliação" até vencer.
