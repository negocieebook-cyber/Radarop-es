# QA do Simulador Manual

A suíte `tests/test_manual_trade_simulator.py` usa somente exemplos `MOCK / TESTE`. Ela confere débito/crédito, perda e ganho máximos, break-even, capital, escala por quantidade e multiplicador, campos ausentes e fonte manual.

A venda coberta registra explicitamente que o risco principal é a queda do ativo. Os testes não representam cotações nem aprovação de operação.
