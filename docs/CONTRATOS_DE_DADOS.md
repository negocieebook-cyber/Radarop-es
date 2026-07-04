# Contratos de Dados

Os contratos abaixo definem os campos mínimos planejados. Eles não autorizam preenchimento por aproximação: valor ausente deve permanecer `None`/“indisponível”, acompanhado da lista de campos faltantes quando impedir um cálculo.

## Classificações comuns

- Tipo: `coletado`, `calculado`, `estimado`, `indisponível` ou `mock/exemplo`.
- Status: `atualizado`, `atrasado`, `incompleto`, `indisponível` ou `mock/exemplo`.
- Linhagem: fonte, tipo, instante de coleta e status.

## Ativo

| Campo | Descrição |
|---|---|
| `ticker` | código de negociação |
| `nome` | nome do emissor/ativo |
| `preco_atual` | último preço válido e sua unidade |
| `fonte` | origem identificável |
| `coleta` | data/hora da coleta |
| `status` | condição de qualidade/atualização |

## Opção

Campos mínimos: `codigo`, `ativo_objeto`, `tipo` (call/put), `strike`, `vencimento`, `premio`, `bid`, `ask`, `volume`, `posicao_em_aberto`, `delta`, `theta`, `iv`, `fonte`, `coleta` e `status`.

Gregas ou IV estimadas precisam informar modelo e ser classificadas como `estimado`. Bid/ask e volume ausentes impedem afirmar liquidez.

## Oportunidade

Campos mínimos: `id`, `ativo`, `estrategia`, `tipo_estrutura`, `vencimento_dias`, `strikes`, `premios`, `ganho_maximo`, `perda_maxima`, `break_even`, `liquidez`, `grafico`, `score`, `decisao`, `fonte` e `tipo_dado`.

Resultados matemáticos devem guardar valores por unidade e, quando houver quantidade, por lote. Score ausente deve ser exibido como “score não calculado”, com motivo.

## Posição

Campos mínimos: `id`, `opportunity_id`, `ativo`, `estrategia`, `data_entrada`, `preco_entrada`, `quantidade`, `status`, `plano_saida`, `fonte_oportunidade` e `tipo_dado`.

O registro local não representa confirmação de corretora e não envia ordens.
