# Controle de Dados

> **REGRA ABSOLUTA: O DASHBOARD NÃO PODE INVENTAR DADO.**

Todo campo deve carregar uma classificação: **coletado**, **calculado**, **estimado**, **indisponível** ou **mock/exemplo**.

1. Todo dado coletado precisa de fonte e timestamp.
2. Todo cálculo precisa de fórmula, unidade, entradas e versão.
3. Todo dado estimado precisa ser marcado como **estimado** e informar o modelo.
4. Todo dado mockado precisa ser marcado como **MOCK / EXEMPLO**.
5. Se faltar dado necessário, não calcular score; mostrar **“score não calculado”**.
6. Se faltar dado crítico, não mostrar o item como oportunidade.
7. Nunca preencher lacunas por média, aproximação ou chute sem que exista uma metodologia aprovada e a marcação “estimado”.

Mensagens padrão: **“indisponível”**, **“não calculado por falta de dados”**, **“fonte ausente”** e **“score não calculado”**.

Na primeira versão, todos os dados da interface são MOCK / EXEMPLO e não representam o mercado.
