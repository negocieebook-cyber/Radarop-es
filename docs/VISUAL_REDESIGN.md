# Visual Redesign

## Nova hierarquia

O app passa a abrir em `Painel de Decisão`, com leitura rápida do que merece atenção imediata.

Ordem da experiência:

1. Aviso global de risco e escopo.
2. Faixa de status dos dados e última atualização.
3. Resumo de decisão:
   oportunidades validadas, quase entradas, acompanhamento, evitar, inconclusivo e primeiro ativo.
4. Três blocos principais:
   `Olhar primeiro`, `Aguardar gatilho` e `Evitar por enquanto`.

## Fluxo do usuário

O usuário deve conseguir responder em poucos segundos:

- existe algo operável;
- qual ativo olhar primeiro;
- o que ainda depende de gatilho;
- o que deve evitar;
- qual validação principal ainda falta.

As páginas detalhadas continuam existindo, mas ficam como apoio:

- `Radar`: motor MOCK / EXEMPLO.
- `Radar EOD`: candidatas reais EOD condicionais.
- `Teses`: leitura gráfica com estratégia prática.
- `Watchlist de Abertura`: acompanhamento de gatilhos salvos.
- `Posições`, `Alertas`, `Simulador`, `Histórico`, `Dados/Config`.

## Card compacto vs detalhe técnico

### Card compacto

Mostra apenas:

- ativo;
- ação prática;
- estratégia sugerida;
- score;
- gatilho;
- invalidação;
- status da cadeia;
- motivo principal;
- botões de detalhe, simulação manual e acompanhamento.

### Detalhes técnicos

Ficam em `expander` e preservam o conteúdo mais denso:

- Healthbox;
- Bulkowski;
- Strategy Screener;
- capital;
- plano manual;
- checklist do book;
- motivos de rejeição;
- campos ausentes.

## Regras para não poluir a tela

- avisos de risco concentrados no topo;
- `NÃO É ORDEM.` curto nos cards;
- blockers, warnings, campos ausentes e screening completo só em expanders;
- não repetir o mesmo aviso em todos os cards;
- não misturar dados MOCK com dados reais;
- não transformar tese em ordem;
- não enviar ordem.

## Status visuais

- verde: validado / ok;
- amarelo: acompanhar / atenção;
- azul: informação / estudo;
- vermelho: evitar / inválido;
- cinza: inconclusivo / sem dados.
