# Base de Dados Bulkowski — Estrutura Inicial

## Objetivo

O catálogo prepara o Radar para organizar padrões gráficos, candles, estudos, rankings, rompimentos, retestes e métodos de alvo. A base atual é manual e inteiramente **MOCK / EXEMPLO**; não houve scraping nem coleta de estatísticas.

## Contrato do padrão

Cada item registra identificação, nome, categoria, tipo, direção teórica, mercado, confirmação necessária, rompimento, pullback/throwback, método de alvo, taxa de falha, movimento médio pós-rompimento, confiabilidade, resumo próprio, fonte, URL de referência, tipo/status do dado e última revisão.

Taxa de falha, movimento médio ou confiabilidade sem coleta verificável recebem **“indisponível”**. O sistema jamais completa essas lacunas por aproximação.

## Uso pelo dashboard

O motor consulta todo o catálogo aplicável, liga um snapshot mockado ao padrão por ID e produz leitura estruturada. A identificação não equivale a confirmação: rompimento, volume e contexto são avaliados separadamente. Sem ID válido, o resultado é **“padrão não detectado”** e a leitura gráfica não confirma a oportunidade.

## Conteúdo e direitos

O projeto não copia texto integral do ThePatternSite. Mantém contratos próprios, resumos autorais curtos e links de referência. Uma futura curadoria deverá registrar origem, data, responsável, direitos de uso, método e revisão de cada campo.

## Estados de análise

- **Padrão detectado:** a geometria/regra candidata foi identificada; ainda pode faltar confirmação.
- **Padrão confirmado:** todos os critérios definidos, como rompimento e volume, foram satisfeitos.
- **Padrão falhado:** ocorreu invalidação objetiva após detecção ou confirmação.
- **Padrão inconclusivo:** dados ou critérios são insuficientes; não deve confirmar decisão.

No futuro, coleta e curadoria devem ocorrer por processo autorizado, rastreável e revisável. Nenhuma estatística publicada entra no sistema sem fonte e validação.
