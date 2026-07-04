# Pipeline Automático

O pipeline atualiza e persiste dados reais sem enviar ordens. `premarket` e `intraday` atualizam mercado e avaliam itens salvos; `close` também atualiza opções EOD e gera oportunidades condicionais.

Execute `python scripts/run_pipeline.py --mode close` ou use `--mode premarket|intraday`. É possível limitar ativos com `--tickers PETR4,VALE3` e vencimentos com `--max-expirations 4`.

Os resultados ficam em `data/runtime/real_opportunities_snapshot.json` e o estado em `data/runtime/pipeline_status.json`. Dados EOD são apenas referência e precisam ser validados no pregão. O Opportunity Engine MOCK permanece separado.
