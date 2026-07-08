# Visual Redesign V2

## Objetivo

Esta revisão reorganiza o Radar de Opções Brasil para uma leitura mais próxima de um painel financeiro profissional, sem alterar motores, cálculos, pipeline ou regras de negócio.

## O que mudou

- Sidebar refeita com fundo escuro, contraste alto e navegação curta.
- Conteúdo principal limitado a largura máxima compacta e centralizada.
- Cabeçalho do Painel de Decisão reduzido a uma linha lógica: título, subtítulo, status e última atualização.
- KPIs reduzidos para quatro indicadores.
- Estado sem dados consolidado em um único bloco central.
- Painel principal reorganizado em grid de duas colunas.
- Cards compactos com detalhes técnicos em expander.

## Nova Hierarquia

### Sidebar

- Painel
  - Visão geral
  - Radar EOD
- Acompanhamento
  - Teses
  - Eventos
  - Posições
  - Alertas
- Ferramentas
  - Simulador
  - Histórico
  - Configurações

### Painel de Decisão

- Cabeçalho compacto
- Aviso global em uma linha
- KPIs
  - Operáveis
  - Aguardando gatilho
  - Eventos próximos
  - Evitar
- Grid principal
  - Coluna 1: Prioridade de hoje, Aguardar gatilho, Evitar por enquanto
  - Coluna 2: Eventos próximos, Qualidade dos dados, Última execução, Avisos importantes

## Regras Visuais

- Sem gradientes.
- Sem sombra pesada.
- Sem fundo bege.
- Sem texto claro sobre fundo claro.
- Sem barras azuis repetidas para estados vazios.
- Sem duplicação entre título da página e menu lateral.

## Cards Compactos

Cada oportunidade prioriza:

- ticker;
- status;
- estratégia;
- score;
- evento próximo;
- gatilho;
- invalidação;
- motivo principal;
- ação para detalhes ou simulação.

Detalhes técnicos permanecem em expander para evitar poluição visual.

## Tema Centralizado

`app/theme.py` concentra:

- paleta;
- tipografia;
- espaçamentos;
- cards;
- badges;
- sidebar;
- empty state;
- comportamento responsivo.

## Garantias Preservadas

- Nenhum dado novo foi inventado.
- MOCK e real continuam separados.
- O painel não envia ordens.
- Teses não são convertidas automaticamente em ordens.
