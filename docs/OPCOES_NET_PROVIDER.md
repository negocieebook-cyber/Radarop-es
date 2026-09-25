# Opções Net Provider (opcoes.net.br)

## Objetivo

Fonte gratuita e sem chave para cadeias de opções EOD e histórico de preços do ativo. Ela é a **primária** na coleta de opções (atualização de cadeias e descoberta do universo) e o histórico gratuito alimenta a Retrospectiva. A brapi continua como **fallback** registrado quando a fonte falha. Nenhum campo ausente é inventado.

## Endpoints utilizados

A API pública usa o formato `GET https://opcoes.net.br/api/v1?z=<época em janela de 10s>&r0t=<Tipo>&r0p.<parametro>=<valor>`:

- `OptionsChain` (params `underlying_asset_id`, `skip`, `load`, `columns_info`, `underlying_quotes=true`): cadeia completa com o bloco `underlying_asset` (`p` preço, `c` variação, `h` data da cotação, `i` volatilidade implícita, `ab`/`mi`/`ma`/`yp`).
- `QuotesHistoryByAsset` (params `assets_ids` — plural — e `timeframe=Day`): histórico diário do ativo (até 3000 candles: `date`, `open`, `high`, `low`, `close`, `change`, `volume`, `vol_impl`, `vol_impl_calls`, `vol_impl_puts`).
- `LastQuotesInfo`: informa `dateLastQuotesInDB` e `hasTodaysQuotesInDB` para rotular honestamente se o banco da fonte já tem o fechamento de hoje.

Não há autenticação nem garantia de SLA: é uma fonte pública de terceiros que pode mudar de formato sem aviso. Por isso cada resposta passa pela normalização com auditoria de campos.

## Normalização

Cada série normalizada registra `symbol`, `side` (call/put), `strike`, `expiration_date`, `last`, `close` (espelho do fechamento EOD), `date`, `volume` (quando a fonte publica), `contracts_quantity`, `financial_volume`, `trades`, posição em aberto (`tit`, `lan`, `cov`, `blk`, `ucov`), gregas (`iv`, `delta`, `gamma`, `theta`, `theta_pct`, `vega`), `moneyness` (letras `I`/`O`/`A` da fonte mapeadas para `ITM`/`OTM`/`ATM`), `liquidity_status` (número de negócios), `normalized_price` com base `last_session`, `price_value_status`, `fonte: opcoes_net_br`, `tipo_dado`, `status_dado`, observação EOD e `campos_ausentes` contra a mesma lista de campos esperados da brapi.

Sem preço do ativo no contexto, moneyness permanece `indisponível`. O preço EOD nunca é apresentado como intraday.

## Fallback para a brapi

No orquestrador de opções (`python scripts/update_options_data.py --mode close`), cada ativo é coletado primeiro pelo opcoes.net.br. Em falha (timeout, JSON inválido, cadeia vazia), o ativo cai para o Brapi Options Provider e o snapshot registra `fallback_from` e `primary_source_error`. A descoberta do universo de opções usa a mesma dupla; ativos sem book/spread publicado recebem classificação de liquidez com aviso explícito de que o book deve ser validado no pregão.

## Histórico datado de cadeias

Cada coleta salva `data/runtime/options_chains_history/{ATIVO}/{AAAA-MM-DD}.json` com o snapshot normalizado do dia (mesmo dia sobrescreve; são mantidos os 30 arquivos mais recentes por ativo). Esse histórico permite acompanhar IV, volume, negócios e posição em aberto entre sessões e alimenta a Retrospectiva.

## Separação do Opportunity Engine

A integração segue as regras do projeto: preço EOD não é executável, candidatas permanecem sujeitas à validação no pregão e nenhuma ordem é enviada. Consulte [Options EOD Orchestrator](OPTIONS_EOD_ORCHESTRATOR.md) e [Auditoria dos Dados de Opções](OPTIONS_DATA_AUDIT.md).
