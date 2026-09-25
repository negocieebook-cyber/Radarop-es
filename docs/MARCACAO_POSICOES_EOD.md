# Marcação de posições com preço real EOD

## Objetivo

Substituir a estimativa pelo preço real da opção no monitor de posições: quando existe cadeia EOD coletada, cada perna é marcada pelo preço da série correspondente (fechamento do dia ou normalizado da última sessão). Sem cadeia, o monitor continua exibindo estimativa honesta e rotulada.

## Como funciona (`app/position_marking.py`)

- **Regras por perna** (`LEG_RULES`): cada estratégia define quais pernas são compradas ou vendidas (por exemplo, call debit spread compra o call e vende o call superior).
- **Pareamento**: a perna da posição casa com a série da cadeia por (`side`, `strike`, `vencimento`) com tolerância de 0,005 no strike. Entre séries idênticas, prioriza a que tem mais negócios registrados.
- **Vencimento**: se o vencimento registrado não tem séries no snapshot (por exemplo, expirado), usa o vencimento futuro mais próximo **que tenha séries** e marca `vencimento_exato: false`.
- **Marcação**: para estruturas de débito, o custo atual é a soma das compras menos as vendas; para estruturas de crédito, o crédito atual é a soma das vendas menos as compras. O P/L por unidade e total é calculado contra o preço de entrada registrado.

## Semântica de entrada

O campo de entrada é sempre **positivo** e o sinal vem do tipo da estrutura:

- **Débito** (call debit spread, put debit spread, long call, long put): `custo_liquido` pago.
- **Crédito** (bull put spread, bear call spread, covered_call): `credito_liquido` / prêmio recebido.

`CREDIT_ENTRY_STRATEGIES` (em `app/position_monitor.py`) é a fonte única dessa lista; o P/L de crédito é `entrada − marcação` e o de débito é `marcação − entrada`.

## Campos exibidos

O monitor de posições mostra as colunas **Marcação da estrutura** (preço atual calculado) e **Base da marcação** (EOD da fonte com data da coleta). A informação na tela avisa que a marcação é EOD, não intraday. No detalhe da posição, uma tabela lista cada perna com o preço encontrado, o strike e o vencimento usado; pernas sem série correspondente ficam listadas em `missing_legs` e o P/L real é suspenso até a cadeia cobrir a estrutura.

## Regras de saída com marcação real

Com a marcação calculada, o monitor aplica as regras objetivas: perda máxima atingida sugere **sair agora**; captura de 75% ou mais do ganho máximo sugere **realizar total**; de 50% a 75% sugere **realizar parcial**. A captura usa o P/L real contra o ganho máximo teórico registrado na entrada. Os alertas apoiam a decisão; nenhuma ordem é enviada.
