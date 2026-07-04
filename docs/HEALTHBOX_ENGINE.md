# Stock Healthbox Engine

## Objetivo

O Healthbox resume a saúde gráfica do ativo e ajuda a verificar se o contexto combina com uma estrutura de opções. É um **filtro**, não uma recomendação isolada, e nunca aprova uma operação sozinho.

## Métricas

Campos fornecidos pelo snapshot: preço atual, abertura, máxima, mínima, fechamento anterior, ADR%, ATR%, rVol, RSI, RSI 200, tendência, suporte, resistência, volatilidade implícita, fonte, coleta e tipo do dado.

Campos calculados: variação diária, range diário e distâncias percentuais assinadas entre preço e suporte/resistência. Cada cálculo retorna `None` quando faltar uma entrada.

## Classificações

- RSI: abaixo de 30 sobrevendido; 30–45 fraco; 45–60 neutro; 60–70 forte; acima de 70 sobrecomprado.
- rVol: abaixo de 0,8 baixo; 0,8–1,2 normal; 1,2–2,0 alto; acima de 2,0 muito alto.
- ATR%: abaixo de 1,5% volatilidade baixa; 1,5%–3,5% normal; acima de 3,5% alta.
- Tendência: alta, baixa, lateral ou indefinida; outros valores são indisponíveis.

Suporte perdido, proximidade da resistência, extremos de RSI e volatilidade são alertas de contexto. A direção adequada depende da estratégia: travas de alta, travas de baixa, venda travada ou venda coberta têm critérios diferentes.

## Estados

- **Healthbox confirma:** todos os critérios mínimos da estratégia foram satisfeitos no snapshot.
- **Healthbox em atenção:** parte do contexto favorece, mas existe alerta ou condição limítrofe.
- **Healthbox não confirma:** o contexto disponível contradiz a estratégia.
- **Healthbox inconclusivo:** faltam dados críticos e nenhuma conclusão deve ser produzida.

## Governança

Nenhum campo ausente é preenchido por chute. Dado fornecido nesta etapa é **MOCK / EXEMPLO**; métricas derivadas são calculadas a partir desses mocks e mantêm essa linhagem. Dados reais futuros precisarão de fonte e timestamp.
