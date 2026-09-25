"""Canônico de status do projeto: rótulos PT-BR e classe CSS por status.

Motores emitem chaves normalizadas (snake_case ou inglês); a camada de UI
traduz e aplica cores usando as funções deste módulo.
"""

from __future__ import annotations

STATUS_LABELS = {
    "approved": "Aprovada",
    "warning": "Atenção",
    "rejected": "Reprovada",
    "info": "Informativo",
    "neutral": "Neutro",
    "entrada_condicional": "Entrada condicional",
    "acompanhar_na_abertura": "Acompanhar na abertura",
    "evitar_por_enquanto": "Evitar por enquanto",
    "evitar": "Evitar",
    "aguardar_gatilho": "Aguardar gatilho",
    "inconclusivo": "Inconclusivo",
    "pendente": "Pendente",
    "compra_operavel": "Compra operável",
    "venda_operavel": "Venda operável",
    "interesse_compra": "Interesse de compra",
    "interesse_venda": "Interesse de venda",
    "neutra_observar": "Neutra, observar",
    "pendente_validacao_opcoes": "Pendente de validação de opções",
    "pendente_dados": "Pendente de dados",
    "sem_dados_eventos": "Sem dados de eventos",
    "apta_graficamente": "Apta graficamente",
    "disponivel_fonte": "Cadeia disponível",
    "indisponivel_fonte": "Fonte indisponível",
}


def status_label(status: object) -> str:
    raw = str(status or "").strip()
    if not raw:
        return "Indisponível"
    key = raw.lower()
    if key in STATUS_LABELS:
        return STATUS_LABELS[key]
    if "_" in raw:
        return raw.replace("_", " ").strip().capitalize()
    return raw


APPROVED_STATUSES = {
    "aprovada",
    "approved",
    "validado",
    "validada",
    "ok",
    "entrada_condicional",
    "compra_operavel",
    "venda_operavel",
    "gatilho acionado",
    "realizar parcial",
    "realizar total",
    "manter",
}

WARNING_STATUSES = {
    "atenção",
    "warning",
    "acompanhar",
    "acompanhar_na_abertura",
    "aguardar_gatilho",
    "aguardando gatilho",
    "perto do gatilho",
    "vencimento próximo",
    "interesse_compra",
    "interesse_venda",
    "neutra_observar",
    "parcial",
    "atualizado com dados parciais",
}

INFO_STATUSES = {"estudo", "informação", "info", "gerado"}

REJECTED_STATUSES = {
    "reprovada",
    "rejected",
    "evitar",
    "evitar_por_enquanto",
    "invalidada",
    "tese invalidada",
    "sair agora",
    "falha na fonte",
    "erro",
}


def status_css_class(status: object) -> str:
    normalized = str(status or "").lower()
    if normalized in APPROVED_STATUSES:
        return "status-approved"
    if normalized in WARNING_STATUSES:
        return "status-warning"
    if normalized in INFO_STATUSES:
        return "status-info"
    if normalized in REJECTED_STATUSES:
        return "status-rejected"
    return "status-neutral"
