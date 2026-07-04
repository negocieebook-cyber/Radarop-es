# Radar de Mercado Real — brapi experimental

O Radar de Mercado consulta preços e histórico OHLCV pela brapi, calcula indicadores e apresenta uma leitura rápida dos ativos no Painel do Dia. Preço e candles são dados **coletados**; RSI, ATR, ADR, rVol, tendência, níveis e distâncias são **calculados** com fonte-base brapi.

O bloco é independente do Opportunity Engine. As oportunidades de opções continuam MOCK / EXEMPLO porque ainda não há cadeia real de opções validada. Nenhum card real deve ser interpretado como oportunidade de opção.

Campos ausentes aparecem como indisponíveis. RSI 200 exige histórico suficiente; volatilidade implícita depende de opções e permanece ausente. Suporte e resistência são extremos simples da janela, não níveis profissionais definitivos.

O cache reduz chamadas repetidas. A idade da coleta é exibida como atualizado, atrasado ou indisponível, sem bloquear o painel nesta etapa. Nenhum valor ausente é preenchido por chute.

Próximos passos: conectar snapshots reais ao Opportunity Engine somente com contratos completos, obter opções reais/licenciadas e gerar oportunidades reais apenas quando preço, liquidez, risco e fonte forem suficientes.
