# Options EOD Orchestrator

## Objetivo

O Options EOD Orchestrator coleta cadeias de opções de vários ativos pela brapi, salva um snapshot independente para cada ativo e registra um resumo da execução. Esta camada é observacional: ela não escolhe estratégias nem gera recomendações.

## Frequência EOD

As cadeias da brapi são dados de fim de pregão, processados após o fechamento. Elas não devem ser interpretadas como bid, ask ou negócios em tempo real intraday.

## Atualização

Para atualizar a lista padrão:

```powershell
python scripts/update_options_data.py --mode close
```

Para informar ativos específicos:

```powershell
python scripts/update_options_data.py --mode close --underlyings PETR4,VALE3,ITUB4,BOVA11 --max-expirations 1
```

A falha de um ativo é registrada e não interrompe os demais.

## Arquivos gerados

- `data/runtime/options_snapshots/{ATIVO}.json`: cadeia e metadados do ativo;
- `data/runtime/options_eod_status.json`: resumo da última execução multiativos.

Um ativo é `disponível` quando a coleta retornou pelo menos uma série normalizada. `indisponível` significa que não havia séries utilizáveis. `erro` registra falha de fonte, autenticação ou acesso; `sem_acesso` indica que o plano/credencial não permitiu a consulta.

Cada série mantém `campos_ausentes`. Bid, ask, gregas, IV, OI ou qualquer outro campo não retornado permanecem indisponíveis; nenhum valor é estimado silenciosamente.

## Limite atual

O Opportunity Engine continua **MOCK / EXEMPLO**. Os snapshots reais não alimentam recomendações nem ordens. Os próximos passos são cruzar as opções EOD com o Market Snapshot, criar um Opportunity Engine real experimental com validações explícitas e, somente depois, avaliar dados intraday ou outro fornecedor se necessário.
