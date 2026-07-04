# Auditoria dos Dados de Opções

## Objetivo

A auditoria verifica o que realmente existe nos snapshots EOD antes de qualquer classificação de entrada. Ela separa campo ausente, campo zerado, valor inválido e possível alias presente no payload bruto.

## Raw e mapeamento

Cada série normalizada preserva `raw` e `raw_keys`. Um campo não mapeado é aquele que existe no raw, mas ainda não possui correspondência validada. Um campo ausente não existe ou veio nulo. Possíveis aliases são apenas reportados; eles não são usados sem que o valor seja numérico e sua origem fique explícita.

## Preço EOD

A resolução tenta `mid` com bid/ask positivos, depois `close`, `average` e aliases reconhecidos no raw. Valores zerados são preservados e auditados, mas não viram preço utilizável. Nenhum preço EOD é tratado como garantia de execução.

## Liquidez

Trades, volume, volume financeiro, bid, ask e spread são auditados separadamente. Aliases como `numberOfTrades`, `quantity` e `businessVolume` são registrados quando aparecem no raw. Ausência de liquidez não é preenchida por estimativa.

## Matemática e pareamento

O relatório identifica preço comprado/vendido ausente, strikes ou vencimento ausentes, largura inválida, prêmios ausentes e erros do cálculo. Por vencimento, informa calls/puts disponíveis, séries com preço e descartes por preço, liquidez ou vencimento.

Execute:

```powershell
python scripts/audit_options_snapshots.py
```

O relatório é salvo em `data/runtime/options_data_audit_report.json`. Depois da auditoria, os próximos passos são validar aliases encontrados, melhorar apenas mapeamentos comprovados e repetir o funil. Inventar preços para aumentar candidatas é proibido.
