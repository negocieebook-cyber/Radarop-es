# Data Provider Engine

## Objetivo

O Data Provider Engine separa coleta, normalização, cache e fallback. A **brapi** é a primeira fonte automática para cotações de ativos e histórico OHLCV. Opções reais ainda não estão integradas e o Opportunity Engine permanece MOCK / EXEMPLO.

## Configuração

Copie `.env.example` para `.env`, informe `BRAPI_TOKEN` e nunca versione o arquivo `.env`. `DATA_PROVIDER=brapi` seleciona o provider. `ALLOW_MOCK_FALLBACK=true` habilita fallback visual explícito; ele nunca é rotulado como dado coletado.

## Cache e erros

Respostas válidas são armazenadas em `data/cache/` com chave e horário UTC. Cache inválido ou vencido é ignorado. Timeout, HTTP não-200 e JSON inválido retornam `success: false`, mensagem clara e `status_dado: erro`, sem quebrar a aplicação.

Campos ausentes permanecem `None`. Dados brapi usam `tipo_dado: coletado`; métricas futuras derivadas usarão `tipo_dado: calculado` e `fonte_base: brapi`. Fallback usa `MOCK / EXEMPLO` e `fallback por erro da fonte real`.

## Próximos passos

- ligar histórico brapi ao Healthbox com fórmulas e janelas documentadas;
- avaliar disponibilidade/licença de opções no plano contratado;
- avaliar fornecedor de opções intraday;
- monitorar atraso, limites e qualidade por endpoint.
