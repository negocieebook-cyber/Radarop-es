# Update Orchestrator

O Update Orchestrator executa e registra coletas reais do Radar de Mercado, sem depender de um clique no Streamlit. Ele usa a brapi somente para ativos e histórico, salva os snapshots em JSON e preserva a linhagem de fonte, coleta, tipo, status e campos ausentes.

## Modos e frequência recomendada

- `premarket`: uma vez antes da abertura;
- `intraday`: a cada 15 minutos;
- posições abertas: a cada 5 a 15 minutos quando houver dados confiáveis;
- `close`: uma vez após o fechamento.

Execute manualmente:

```powershell
python scripts/update_market_data.py --mode intraday
python scripts/update_market_data.py --mode premarket --tickers PETR4,VALE3
python scripts/update_market_data.py --mode close
```

Os dados ficam em `data/runtime/market_snapshots.json`; execuções e erros ficam em `data/runtime/update_status.json`. Uma falha da fonte é registrada e nunca é preenchida silenciosamente com dado inventado ou mock.

## Agendamento futuro

O script pode ser chamado por GitHub Actions, cron em VPS ou um job agendado em Render. Essa infraestrutura ainda não está configurada; o segredo `BRAPI_TOKEN` deverá ficar no gerenciador de secrets do ambiente e jamais em logs ou no repositório.

Atualizar o Radar apenas coleta e calcula o contexto dos ativos. Gerar oportunidade exige cadeia de opções, liquidez, strikes e preços confiáveis. Como opções reais ainda não foram integradas, o Opportunity Engine permanece **MOCK / EXEMPLO** e não usa estes snapshots para sugerir operações.
