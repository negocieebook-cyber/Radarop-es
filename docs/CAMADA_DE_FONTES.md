# Camada de Fontes e Confiabilidade

## Por que ela existe

O registro separa o dado da sua origem e impede que a interface trate uma intenção de integração como fonte ativa. Cada origem precisa declarar uso, status, custo, frequência, confiabilidade, campos esperados e última coleta.

## Regra central

O sistema não inventa dados. Fonte futura não é fonte implementada; registro no catálogo não significa que houve conexão ou coleta. A versão atual não possui coleta real.

## Tipos de dado

- **Coletado:** veio de fonte implementada, com referência e timestamp.
- **Calculado:** resultado de fórmula versionada sobre entradas rastreáveis.
- **Estimado:** resultado de modelo identificado, sempre rotulado.
- **Indisponível:** fonte ou valor não existe para o contexto.
- **Mock/exemplo:** valor demonstrativo que não representa o mercado.

## Entrada de uma fonte

Uma fonte deve ser cadastrada, ter metadados completos, direitos e custo avaliados, contrato de campos definido, testes de integridade, política de atraso e falha, monitoramento e aprovação explícita antes de mudar para `implementado`.

## Contratos e falhas

Os contratos retornam validade e campos ausentes; nunca completam o registro. Sem campo crítico, cálculo e score ficam bloqueados. A interface deve exibir “indisponível”, “fonte ausente” ou “não calculado por falta de dados”.

Uma oportunidade não pode ser publicada como real quando preço, opção, liquidez, risco ou fonte crítica estiver ausente. Preservar essa barreira é mais importante que preencher o painel.
