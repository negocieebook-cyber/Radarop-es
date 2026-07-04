# Descoberta do Universo de Opções

O discovery testa, sob demanda, quais ativos possuem cadeias de opções EOD acessíveis pela fonte atual e salva o resultado em `data/runtime/options_universe_availability.json`.

Use `python scripts/discover_options_universe.py --limit 20` ou informe `--tickers PETR4,VALE3`. O pipeline apenas lê caches com até 72 horas; ele não repete a descoberta em todo fechamento. Falhas e acessos negados permanecem explícitos e não viram dados simulados.
