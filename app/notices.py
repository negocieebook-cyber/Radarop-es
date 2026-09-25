"""Avisos compartilhados entre páginas (fonte única, sem repetição de textos)."""

from __future__ import annotations

RISK_NOTICE = (
    "Este painel não envia ordens. Dados EOD precisam ser validados no book. "
    "Prêmio não é lucro garantido."
)
EOD_OPTIONS_NOTICE = (
    "Dados de opções são EOD/fim de pregão. Esta seção não indica entrada imediata. "
    "Ela mostra estruturas condicionais para validar no pregão. Não envia ordens."
)
NO_BROKER_NOTICE = "Nenhuma ordem é enviada e não há conexão com corretora."
