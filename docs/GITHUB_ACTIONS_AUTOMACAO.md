# Automação com GitHub Actions

## Objetivo

O workflow `.github/workflows/update-market-data.yml` executa o Update Orchestrator sem depender de um computador local. Ele consulta a brapi, atualiza os snapshots persistidos e commita somente os arquivos de runtime previstos.

O token nunca deve ser colocado no código, no workflow ou em um arquivo `.env` versionado.

## Como funciona

Em cada execução, o GitHub Actions:

1. baixa o repositório e configura o Python 3.11;
2. instala `requirements.txt`;
3. confirma que o secret `BRAPI_TOKEN` existe, sem imprimir seu valor;
4. escolhe o modo `premarket`, `intraday` ou `close`;
5. executa `python scripts/update_market_data.py --mode <modo>`;
6. adiciona somente os dois JSONs de runtime e cria o commit `Atualiza snapshots de mercado` quando houver mudanças.

Se a brapi falhar, o orchestrator registra a falha em `update_status.json`. O workflow ainda tenta salvar esse estado no repositório e, em seguida, termina com erro visível. O fallback mock fica desativado na automação e nenhum dado é inventado.

## Horários sugeridos

As agendas rodam de segunda a sexta-feira:

- pré-pregão: 12:30 UTC;
- intraday: a cada 15 minutos, de 13:00 até 20:45 UTC;
- pós-fechamento: 21:30 UTC.

Os horários do GitHub Actions são UTC. Brasília normalmente está em UTC-3; revise as agendas caso o horário desejado ou as regras de mercado mudem. Execuções agendadas podem começar com atraso em períodos de alta demanda do GitHub.

## Configurar o secret da brapi

No GitHub:

`Settings > Secrets and variables > Actions > New repository secret`

- Name: `BRAPI_TOKEN`
- Value: sua chave da brapi

O workflow falha com uma mensagem clara se esse secret estiver ausente. Ele apenas informa que o secret foi detectado e não imprime seu conteúdo.

## Rodar manualmente

Abra a aba **Actions**, selecione **Atualizar dados de mercado**, clique em **Run workflow** e escolha um modo:

- `premarket`;
- `intraday`;
- `close`.

## Arquivos atualizados

- `data/runtime/market_snapshots.json`: último conjunto de snapshots reais coletados;
- `data/runtime/update_status.json`: resultado por modo, horários e eventual erro da coleta.

A dashboard lê o último snapshot salvo. Isso é atualização automática periódica, não streaming nem tempo real: entre duas execuções, o conteúdo permanece igual. O GitHub Actions também pode atrasar, sofrer limites de uso, indisponibilidade externa ou conflitos com proteções da branch. Se a branch exigir revisão ou bloquear pushes do bot, será necessário ajustar as permissões do repositório.

## Limites atuais

O Opportunity Engine e todos os dados de opções continuam **MOCK / EXEMPLO**. Opções reais não estão integradas, nenhuma corretora é conectada e nenhuma ordem é enviada.
