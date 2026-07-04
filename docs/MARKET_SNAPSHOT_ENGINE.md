# Market Snapshot Engine

O módulo combina cotação e histórico OHLCV da brapi para criar snapshots reais/experimentais aceitos pelo Stock Healthbox. Valores recebidos são `coletado`; RSI, ATR, ADR, rVol, tendência, níveis e distâncias são `calculado` com `fonte_base: brapi`.

Indicadores: variação diária, range diário, RSI 14, RSI 200 quando houver ao menos 201 fechamentos, ATR% 14, ADR% 14, volume relativo 20, médias 9/21 e suporte/resistência simples de 20 candles.

Suporte e resistência são apenas menor mínima e maior máxima da janela. Não representam análise profissional definitiva. Histórico insuficiente ou candle incompleto retorna `None`, status `indisponível` e motivo; nenhuma lacuna é estimada.

Se houver cotação sem histórico, o snapshot é preservado como incompleto. Se ambos falharem, o status é erro. Fallback só aparece quando habilitado no Provider Manager e mantém rótulo MOCK / EXEMPLO.

O Opportunity Engine continua inteiramente mockado. Próximos passos: avaliar snapshots reais no funil, obter opções reais/licenciadas e ligar alertas de posições a preços coletados.
