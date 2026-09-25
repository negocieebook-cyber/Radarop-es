# Status das atualizações

## Horários

Os arquivos gravam os horários em UTC. A interface exibe os horários convertidos para o horário de Brasília (UTC-3), identificados pelo sufixo `(Brasília)`. Vales de horário sem fuso informado aparecem como estão, sem conversão suposta.

## Arquivos persistidos

Os snapshots de mercado ficam em `data/runtime/market_snapshots.json`. Cada snapshot mantém a fonte, a data/hora de coleta, o `status_dado` e a lista `campos_ausentes`; campos reais ausentes não são preenchidos com valores inventados.

O histórico operacional da atualização fica em `data/runtime/update_status.json`, separado por modo (`premarket`, `intraday` e `close`). Ele registra horários, contagens, erros, fonte e origem da execução.

## Runner

O campo `runner` identifica quem iniciou a atualização:

- `streamlit_app`: botão **Atualizar agora** da dashboard;
- `local_script`: comando executado no computador local;
- `github_actions`: rotina automática do GitHub, detectada por `GITHUB_ACTIONS=true`.

O runner informa a origem da execução, não a origem dos dados. A fonte é registrada separadamente: `brapi` para mercado e `opcoes_net_br` ou `brapi_options` para cadeias de opções (com fallback registrado quando a primária falha).

## Estados dos dados

`incompleto` significa que houve resposta ou snapshot utilizável, mas um ou mais campos esperados ficaram ausentes. Esses campos devem ser consultados em `campos_ausentes`.

`erro` significa que a fonte falhou ou não forneceu dados utilizáveis. O erro não é escondido e fica registrado em `errors` e `last_error`. O app permanece disponível, sem substituir silenciosamente a falha por mock.

A idade do último snapshot é classificada assim:

- `atualizado`: menos de 20 minutos;
- `atrasado`: de 20 a 90 minutos;
- `muito atrasado`: mais de 90 minutos;
- `indisponível`: nenhuma data válida foi registrada.

Essa classificação é apenas informativa e ainda não bloqueia nenhuma ação.

## Camada de decisão real EOD

O Radar de Fechamento cruza snapshots de mercado, Healthbox real e cadeias de opções EOD em uma camada experimental de decisão com bloqueios e avisos honestos: preço EOD não é executável, candidatas devem ser confirmadas no pregão e nenhuma ordem é enviada. Os motores MOCK / EXEMPLO continuam disponíveis na página Demonstração, separados sem mistura silenciosa de fontes.
