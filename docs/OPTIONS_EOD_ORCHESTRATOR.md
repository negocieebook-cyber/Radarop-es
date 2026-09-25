# Options EOD Orchestrator

## Objetivo

O Options EOD Orchestrator coleta cadeias de opções de vários ativos — fonte primária opcoes.net.br com fallback brapi — salva um snapshot independente para cada ativo e registra um resumo da execução. Esta camada é observacional: ela não escolhe estratégias nem gera recomendações.

## Frequência EOD

As cadeias são dados de fim de pregão, processados após o fechamento. Elas não devem ser interpretadas como bid, ask ou negócios em tempo real intraday. O `LastQuotesInfo` da fonte informa a data do último fechamento no banco e se a coleta de hoje já aconteceu, e esse status vai para o resumo da execução.

## Atualização

Para atualizar a lista padrão:

```powershell
python scripts/update_options_data.py --mode close
```

Para informar ativos específicos:

```powershell
python scripts/update_options_data.py --mode close --underlyings PETR4,VALE3,ITUB4,BOVA11 --max-expirations 1
```

A falha de um ativo é registrada e não interrompe os demais. Em falha do opcoes.net.br, o ativo cai para a brapi e o snapshot registra `fallback_from` e `primary_source_error`.

## Arquivos gerados

- `data/runtime/options_snapshots/{ATIVO}.json`: cadeia e metadados do ativo;
- `data/runtime/options_chains_history/{ATIVO}/{AAAA-MM-DD}.json`: histórico datado (30 dias por ativo), usado pela Retrospectiva e para acompanhar IV, volume, negócios e posição em aberto entre sessões;
- `data/runtime/options_eod_status.json`: resumo da última execução multiativos, incluindo `quotes_info` da fonte e a fonte usada por ativo.

Um ativo é `disponível` quando a coleta retornou pelo menos uma série normalizada. `indisponível` significa que não havia séries utilizáveis. `erro` registra falha de fonte, autenticação ou acesso; `sem_acesso` indica que o plano/credencial não permitiu a consulta.

Cada série mantém `campos_ausentes`. Bid, ask, gregas, IV, OI ou qualquer outro campo não retornado permanecem indisponíveis; nenhum valor é estimado silenciosamente.

## Limite atual

Os snapshots reais alimentam a camada experimental de decisão (Radar EOD, marcação de posições e retrospectiva), que permanece sujeita à validação no pregão e não envia ordens. Os próximos passos são ampliar cobertura de ativos, melhorar leitura de liquidez e avaliar dados intraday se necessário.
