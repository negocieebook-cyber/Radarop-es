# Radar de Opções Brasil

Dashboard diária para apoiar a análise de oportunidades em opções do mercado brasileiro. O projeto organiza informações de liquidez, risco, vencimento, strikes, prêmio, break-even, perda e ganho máximos, leitura gráfica, Stock Healthbox e referências do ThePatternSite/Bulkowski.

> **Estado atual:** a brapi alimenta o Radar de Mercado e seus snapshots reais são salvos localmente. O Opportunity Engine e todas as informações de opções continuam **MOCK / EXEMPLO**.

## Objetivo

Transformar dados rastreáveis em uma rotina objetiva de estudo, acompanhamento e saída de operações. O sistema deverá distinguir dados coletados, calculados, estimados, indisponíveis e mockados, sem preencher lacunas com suposições.

## Módulos principais

- Painel do Dia e ranking de oportunidades;
- análise de estratégias com risco definido;
- Stock Healthbox;
- leitura gráfica baseada em Bulkowski/ThePatternSite;
- checklist de qualidade e controle de fontes;
- acompanhamento de posições, alertas de saída e histórico.
- núcleo determinístico de qualidade, validação, matemática de opções e score explicável.
- catálogo estrutural Bulkowski/ThePatternSite com padrões e análises MOCK / EXEMPLO, sem scraping.
- Stock Healthbox calculado sobre snapshots MOCK / EXEMPLO, usado apenas como filtro contextual.
- registro de fontes futuras, confiabilidade e contratos mínimos de dados, sem conectores ativos.
- Position Monitor / Exit Engine com P/L, captura de ganho e alertas explicáveis sobre contexto MOCK / EXEMPLO.
- Opportunity Engine que cruza universo, cadeia, risco, liquidez, Healthbox e Bulkowski para aprovar ou reprovar candidatos mockados.
- fluxo diário com filtros, detalhe auditável da oportunidade e acompanhamento organizado.
- interface premium em dark mode com hierarquia visual e status por cor.
- Data Provider Engine com brapi para testes manuais de preços/histórico e cache local.
- Market Snapshot Engine e Healthbox real experimental com indicadores calculados sobre histórico brapi.
- Radar de Mercado real/experimental no Painel do Dia, separado das oportunidades mockadas.
- Update Orchestrator para persistir snapshots reais e registrar execuções e erros por modo.

As decisões da versão demonstrativa são persistidas localmente em `data/positions.json` e `data/history.json`. Esses registros continuam classificados como **MOCK / EXEMPLO** e não representam ordens ou posições de corretora.

Para validar o núcleo sem iniciar a interface:

```powershell
python scripts/validate_project.py
```

## Status atual e próximos passos

O projeto possui interface, persistência local de decisões mockadas, matemática de opções, validações, score, Bulkowski estrutural, Healthbox e camada de fontes/contratos. **Todos os dados de mercado continuam MOCK / EXEMPLO.** A camada de fontes é somente governança; nenhuma coleta real está ativa.

Próximos passos possíveis: definir licenças e fornecedores, implementar um conector por vez, validar timestamps e integridade, criar testes automatizados e somente então habilitar dados coletados na interface.

## Configurar a brapi

Copie `.env.example` para `.env`, substitua `BRAPI_TOKEN` pela sua chave local e reinicie o Streamlit. **Nunca commite o arquivo `.env` ou um token real.** Na aba Configurações, use os botões de teste da brapi. O Opportunity Engine e as opções continuam usando somente MOCK / EXEMPLO nesta etapa.

Na mesma aba, a seção **Healthbox Real — brapi experimental** cria snapshots reais sob demanda. Opções reais ainda não foram integradas e nenhum indicador ausente é inventado.

Para atualizar e persistir o Radar de Mercado fora do Streamlit:

```powershell
python scripts/update_market_data.py --mode intraday
```

Os snapshots reais ficam em `data/runtime/market_snapshots.json` e o estado das rotinas em `data/runtime/update_status.json`. O Opportunity Engine permanece mockado e opções reais ainda não foram integradas.

## Atualização automática

O projeto inclui um GitHub Actions agendado para executar o Update Orchestrator em modos de pré-pregão, intraday e pós-fechamento. Para ativá-lo, crie no repositório o secret `BRAPI_TOKEN` em **Settings > Secrets and variables > Actions**. O token não deve ser colocado no código nem em arquivos versionados.

As agendas de segunda a sexta rodam às 12:30 UTC (pré-pregão), a cada 15 minutos entre 13:00 e 20:45 UTC (intraday) e às 21:30 UTC (pós-fechamento). O workflow salva e commita `data/runtime/market_snapshots.json` e `data/runtime/update_status.json`; a dashboard lê o último snapshot persistido.

Essa rotina é periódica, não uma conexão em tempo real. O Opportunity Engine e os dados de opções continuam **MOCK / EXEMPLO**. Consulte [a documentação da automação](docs/GITHUB_ACTIONS_AUTOMACAO.md) para configurar o secret e executar o workflow manualmente.

A dashboard exibe o modo, a origem (`streamlit_app`, `local_script` ou `github_actions`), as contagens e a idade da atualização. Consulte [Status das atualizações](docs/STATUS_ATUALIZACAO.md) para interpretar snapshots incompletos, erros e atrasos.

## Teste de opções EOD

O Brapi Options Provider permite testar vencimentos e cadeias EOD sem conectá-los ao radar de oportunidades. O teste salva um snapshot isolado, informa erros de API ou falta de acesso do plano e nunca completa campos ausentes com dados inventados.

O Opportunity Engine continua **MOCK / EXEMPLO**. O próximo passo, condicionado à validação de acesso e qualidade, será decidir entre integrar a cadeia real ou avaliar outro fornecedor. Consulte [Brapi Options Provider](docs/BRAPI_OPTIONS_PROVIDER.md).

## Options EOD Orchestrator

O projeto agora coleta e salva cadeias EOD reais da brapi separadamente por ativo, continuando mesmo quando um ativo falha ou não possui séries. Execute:

```powershell
python scripts/update_options_data.py --mode close
```

Estado atual: ações reais via brapi, opções reais EOD via brapi e Opportunity Engine ainda **MOCK / EXEMPLO**. Recomendações reais permanecem desativadas. Consulte [Options EOD Orchestrator](docs/OPTIONS_EOD_ORCHESTRATOR.md).

## Opportunity Engine Real Experimental

Uma seção separada cruza market snapshots reais, Healthbox real e opções EOD para classificar estudos como `estudar`, `atenção`, `evitar` ou `inconclusivo`. Ela não é tempo real, não confirma entradas e não envia ordens. O Opportunity Engine mockado continua existindo sem mistura silenciosa de fontes.

Consulte [Opportunity Engine Real Experimental](docs/REAL_OPPORTUNITY_ENGINE.md) para as regras de preço indicativo, estratégias permitidas e critérios de decisão.

## Entradas Condicionais EOD

O Conditional Entry Engine acrescenta limites de débito/crédito, condições de confirmação e regras de invalidação às candidatas reais EOD. “Entrada condicional” significa observar e validar no pregão; o preço EOD não é executável nem representa entrada imediata.

Próximos passos: adicionar Bulkowski real, melhorar a leitura de liquidez, testar mais ativos com opções e avaliar dados intraday no futuro. Consulte [Conditional Entry Engine](docs/CONDITIONAL_ENTRY_ENGINE.md).

## Diagnóstico do funil real EOD

A coleta de opções pode analisar até quatro vencimentos entre 7 e 60 dias, priorizando 15 a 45 dias. O painel explica os principais motivos de reprovação e destaca “quase entradas”: estruturas matematicamente completas que ainda precisam melhorar preço, liquidez ou confirmação contextual.

Consulte [Diagnóstico do Funil Real EOD](docs/FUNIL_DIAGNOSTICO_REAL_EOD.md).

## Auditoria de opções

Os snapshots de opções preservam o payload bruto e passam por auditoria de preço, liquidez e entradas de pareamento. Campos ausentes, zerados, inválidos e possíveis aliases são reportados separadamente em `data/runtime/options_data_audit_report.json`.

Execute `python scripts/audit_options_snapshots.py` ou consulte o subpainel de auditoria na seção real EOD. Veja [Auditoria dos Dados de Opções](docs/OPTIONS_DATA_AUDIT.md).

## Calibração de decisão

O funil real separa hard blockers de soft warnings. Bloqueios matemáticos, preço ausente, liquidez ilíquida e snapshots indisponíveis continuam impedindo entradas; alertas de preço EOD, Healthbox neutro e liquidez intermediária podem levar a **acompanhar na abertura**.

As faixas de tolerância são limitadas a 15% acima do débito máximo e 15% abaixo do crédito mínimo. Consulte [Calibração de Decisão](docs/DECISION_CALIBRATION.md).

## Limites do sistema

O Radar é uma ferramenta de **apoio à decisão**, não uma recomendação automática. Ele não envia ordens, não opera por conta do usuário e não substitui análise própria. O investidor é responsável pela decisão final.

## Executar localmente

Requer Python 3.10 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Consulte as regras e os módulos planejados na pasta `docs/`.
# Pipeline automático de oportunidades reais EOD

O comando `python scripts/run_pipeline.py --mode close` atualiza mercado, opções EOD e salva oportunidades condicionais em `data/runtime/real_opportunities_snapshot.json`. Os modos `premarket` e `intraday` atualizam mercado e monitoramento, sem gerar novas oportunidades EOD.

A dashboard lê o último snapshot persistido. Dados EOD não são tempo real e devem ser validados no pregão. O Opportunity Engine MOCK permanece separado. Consulte `docs/PIPELINE_AUTOMATICO.md`.

## Descoberta do universo de opções

`python scripts/discover_options_universe.py --limit 20` testa quais ativos possuem cadeias EOD acessíveis e grava um cache por até 72 horas. O pipeline usa os ativos disponíveis desse cache; sem cache válido, mantém a lista padrão. A descoberta não roda em todo fechamento.

O universo brasileiro ampliado fica em `data/option_candidate_tickers.json`. Use `python scripts/discover_options_universe.py --from-candidates --batch-size 15 --include-low-liquidity true`; cada lote salva um checkpoint e execuções posteriores pulam tickers recentes. `--force` solicita um novo teste. “Sem acesso pela fonte” não significa ausência de opções na B3.

## Radar Gráfico de Regiões

O pipeline gera teses para um universo de mercado mais amplo reutilizando Healthbox e Bulkowski. Estrutura, delta-alvo e vencimento são sugestões para validação: delta real não é calculado sem cadeia e nenhuma tese representa ordem. O resultado fica em `data/runtime/graphical_theses_snapshot.json`.

Por padrão, `--graphical-limit 30` usa `data/graphical_candidate_tickers.json`, quando existir, ou recua para o universo candidato de opções. Os estados intermediários `interesse_compra` e `interesse_venda` indicam proximidade de setup, nunca uma entrada.

O diagnóstico separa blockers técnicos de confirmações ausentes e cria um `near_setup_score` para ordenar até dez quase setups. O ranking é explicativo: não promove tese a entrada nem afrouxa os critérios de compra/venda operável.

A aba **Teses Gráficas** mantém uma watchlist persistente em
`data/runtime/graphical_watchlist.json`. O pipeline reavalia gatilho,
proximidade e invalidação com snapshots salvos, sem transformar a tese em
entrada, depender da cadeia de opções ou enviar ordens. Consulte
`docs/GRAPHICAL_WATCHLIST.md`.

O **Strategy Mapper** reutiliza Healthbox, Bulkowski e as teses gráficas para
classificar regimes direcionais, lateralidade e compressão. As famílias de
estratégias permanecem pendentes sem cadeia e nunca são aprovadas sem preço,
liquidez, break-even e perda máxima. Consulte `docs/STRATEGY_MAPPER.md`.

O **Strategy Screener** avalia as 21 estratégias de
`app/options_strategy_catalog.py` para cada tese, registra candidatas,
pendências e rejeições e mantém qualquer estrutura sem cadeia ou matemática
completa fora do estado validado. Consulte `docs/STRATEGY_SCREENER.md`.

Cada avaliação do Screener inclui um **Plano de Validação Manual** com
`delta_alvo`, região relativa de strikes, vencimento, checklist do book e
regras de rejeição. Sem cadeia, não são criados strikes, preços ou deltas reais;
limites monetários permanecem indisponíveis até o motor receber dados válidos.

O **Modo Prático** resume cada tese em melhor estratégia, top 3, ação diária e
plano curto para o book. O Radar Gráfico oferece filtros por regime, status,
estratégia e ação; as 25 avaliações continuam disponíveis no expander
**Ver screening completo**.

Cada estratégia também recebe uma etiqueta de **objetivo**: prêmio, direção,
proteção, carteira, lateralidade, volatilidade/evento, estudo avançado ou
esperar. A etiqueta é explicativa; prêmio não é lucro garantido e nenhuma
estrutura é aprovada sem cadeia, preço, liquidez e perda máxima.

O painel **Prioridades por Objetivo** organiza até cinco itens por categoria
para indicar o que olhar primeiro. Ele não aprova operações: score, delta-alvo,
região de strike e ação prática continuam sujeitos à validação de cadeia,
preço, liquidez, spread, break-even e perda máxima.
### Capital e encaixe no perfil

O Strategy Screener mostra capital técnico mínimo, capital recomendado, perda máxima estimada e encaixe no perfil informado. Sem multiplicador, preço, strikes, custo/crédito ou perda máxima vindos de fonte real, a classificação fica pendente. O multiplicador padrão só é usado quando o usuário opta explicitamente. Essas estimativas não aprovam operações nem substituem a margem exigida pela corretora; o painel apenas organiza o que olhar primeiro e mantém casos apertados visíveis.

### Simulador manual

A aba **Simulações Manuais** recebe strikes, prêmios, vencimento, quantidade e multiplicador vistos pelo usuário no book. Os resultados ficam marcados como `manual`, podem ser salvos localmente e nunca geram ordens. Capital, perda máxima, ganho máximo e break-even só aparecem quando os campos necessários permitem cálculo determinístico.

Os cálculos principais possuem auditoria didática em `tests/test_manual_trade_simulator.py`. As fixtures são identificadas como `MOCK / TESTE` e não são dados reais de mercado.
