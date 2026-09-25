# Notificações por Telegram

## Objetivo

Levar o resumo diário da rotina para fora do dashboard, sem recomendação e sem ordens: estado das atualizações, contagem de oportunidades, watchlist, posições e retrospectiva.

## Configuração

- **Aba Configurações > Rotinas**: informe o token do bot e o chat_id, escolha ativar e salve. A configuração fica em `data/secrets/telegram.json` (nunca commitada; `data/secrets/` deve estar fora do versionamento). O token é exibido mascarado e nunca aparece em logs ou na resposta da API.
- **Variáveis de ambiente**: `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` preenchem campos ausentes quando não existe arquivo local. O arquivo local tem precedência.

## Como criar o bot

No Telegram, converse com o BotFather (`/newbot`), guarde o token e envie qualquer mensagem ao bot (ou ao canal/grupo escolhido). O chat_id pode ser obtido por ferramentas públicas de consulta à API do Telegram. O bot precisa ter permissão para escrever no chat de destino.

## Digest diário

O digest (montado em `app/notify_engine.py`) resume, com status honesto e sem dados inventados:

- atualização de mercado, de opções EOD e do pipeline (status, horário e fonte);
- cotações no banco da fonte (se o fechamento de hoje já foi coletado);
- contagens do Radar EOD (estudar, atenção, evitar, inconclusivo, entrada condicional, acompanhar na abertura);
- watchlist da Abertura em andamento, posições registradas e retrospectiva estimada.

## Formas de envio

- **Botão da aba Rotinas**: "Enviar digest de teste agora" envia imediatamente; "Apagar configuração" remove o arquivo local.
- **Script**: `python scripts/send_daily_digest.py` (saída 0 = enviado, 1 = falha no envio, 2 = não configurado).
- **GitHub Actions**: crie os secrets `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` no repositório. O workflow de atualização envia o digest ao fim do modo `close` apenas quando os dois secrets existem; sem eles, o passo é pulado sem erro.

O digest é informativo: nenhuma ordem é enviada e o app continua funcionando normalmente sem qualquer configuração de Telegram.
