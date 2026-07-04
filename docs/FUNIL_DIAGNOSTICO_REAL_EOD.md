# Diagnóstico do Funil Real EOD

## Objetivo

O diagnóstico explica por que candidatas reais EOD foram classificadas como entrada condicional, acompanhar, evitar ou inconclusivo. Evitar não é falha do motor: é o resultado correto quando preço, matemática, liquidez, vencimento ou contexto não atendem aos critérios.

## Múltiplos vencimentos

Analisar apenas o vencimento mais próximo tende a concentrar estruturas com pouco tempo para ajuste. A coleta seleciona até quatro vencimentos entre 7 e 60 dias, priorizando a faixa de 15 a 45 dias. Cada cadeia permanece separada para impedir pareamento entre vencimentos diferentes.

Faixas usadas na decisão:

- menos de 5 dias: evitar;
- 5 a 10 dias: somente acompanhar;
- 11 a 45 dias: faixa preferida;
- 46 a 60 dias: aceitável, com atenção à liquidez;
- acima de 60 dias: evitar nesta fase inicial.

## Quase entrada

Uma quase entrada possui matemática completa, perda e ganho máximos, break-even e vencimento observável, mas ainda falha em poucos critérios. O painel mostra o principal motivo e o que precisaria mudar, como redução do débito, aumento do crédito, melhora da liquidez ou confirmação do Healthbox.

Os motivos são padronizados e incluem vencimento curto, liquidez insuficiente, preço EOD indicativo, custo acima do máximo, crédito abaixo do mínimo, risco/retorno ruim, Healthbox contrário, snapshot ausente, acesso negado, preço indisponível e matemática incompleta.

## Uso no dia seguinte

Use o diagnóstico para formar uma lista de observação e confirmar preços, spread, liquidez e contexto na abertura. Dados EOD não são executáveis e não autorizam entrada automática. Nenhum campo ausente é inventado, nenhuma corretora é conectada e nenhuma ordem é enviada.
