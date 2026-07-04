# Brapi Options Provider

## Objetivo

Este módulo testa, de forma isolada, se a credencial local da brapi permite consultar vencimentos e cadeias de opções brasileiras. Ele não alimenta o Opportunity Engine e não gera recomendações.

## Endpoints

O provider está preparado para:

- `GET /api/v2/options/expirations`: vencimentos do ativo subjacente;
- `GET /api/v2/options/chain`: séries negociadas no vencimento;
- `GET /api/v2/options/historical`: histórico de uma série;
- `/analytics` e `/analytics/history`: reservados para uma etapa futura, sem uso atual.

A brapi informa que os dados de opções são EOD, processados após o encerramento do pregão. Eles não representam cotação intraday em tempo real. O acesso amplo pode exigir o plano Pro; o sandbox da fonte pode ter cobertura limitada.

## Normalização e integridade

A cadeia normaliza contrato, OHLC, bid, ask, negócios, volume e volume financeiro. `mid` só é calculado quando bid e ask existem; o spread percentual também exige um `mid` diferente de zero. A liquidez é classificada pela quantidade de negócios.

Cada série registra `fonte`, `tipo_dado`, `status_dado`, observação EOD e `campos_ausentes`. O módulo não inventa gregas, volatilidade implícita, posição em aberto ou moneyness. Sem preço do ativo no contexto, moneyness permanece `indisponível`.

## Erros e acesso

Falhas 401, 403, 404, 429, 500, timeout e JSON inválido retornam uma estrutura segura e não quebram o app. Respostas 401 ou 403 recebem `access_status: sem_acesso`; a interface orienta verificar se o plano inclui opções. Nenhum fallback mock é apresentado como dado real.

Os arquivos persistidos são:

- `data/runtime/options_chain_snapshot.json`;
- `data/runtime/options_update_status.json`.

## Separação do Opportunity Engine

O Opportunity Engine continua **MOCK / EXEMPLO** até que cobertura, completude, licença, atualização e qualidade das cadeias reais sejam validadas. Se houver acesso adequado, o próximo passo será criar uma integração explícita e testada. Sem acesso, deve-se avaliar um fornecedor pago, mantendo oportunidades mockadas separadas.
