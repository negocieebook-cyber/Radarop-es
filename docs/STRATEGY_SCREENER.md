# Strategy Screener

O Screener avalia todas as estratégias do catálogo contra o regime produzido
pelo Strategy Mapper, Healthbox, Bulkowski e níveis da tese gráfica.

Compatibilidade gráfica não é aprovação. Estratégias sem cadeia e matemática
completa ficam pendentes; perda máxima, break-even, preço, spread e liquidez
devem ser validados antes de qualquer operação. Delta sem cadeia é somente
`delta_alvo`.

O catálogo descreve 25 estratégias com explicação, pernas, tese ideal,
condições de uso e rejeição, dados e cálculos obrigatórios. Estratégias de
venda aparecem apenas cobertas ou travadas; `synthetic_short_stock` é rejeitada
por padrão e mantida somente para estudo teórico avançado.
