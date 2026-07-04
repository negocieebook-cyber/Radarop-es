"""Catálogo declarativo de estratégias avaliadas pelo Strategy Screener."""

from __future__ import annotations

from typing import Any


def _strategy(
    strategy_id: str,
    nome: str,
    categoria: str,
    regime_ideal: list[str],
    direcao: str,
    complexidade: str,
    *,
    exige_ativo: bool = False,
    exige_caixa: bool = False,
    risco_definido: bool = True,
    delta_alvo_padrao: str | None = None,
    vencimento_ideal: str = "15 a 45 dias, sujeito à validação da cadeia",
    quando_usar: str,
    quando_evitar: str,
    dados_obrigatorios: list[str] | None = None,
    alertas: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": strategy_id,
        "nome": nome,
        "categoria": categoria,
        "regime_ideal": regime_ideal,
        "direcao": direcao,
        "complexidade": complexidade,
        "exige_ativo": exige_ativo,
        "exige_caixa": exige_caixa,
        "exige_cadeia_real": True,
        "risco_definido": risco_definido,
        "perda_maxima_obrigatoria": True,
        "delta_alvo_padrao": delta_alvo_padrao,
        "vencimento_ideal": vencimento_ideal,
        "quando_usar": quando_usar,
        "quando_evitar": quando_evitar,
        "dados_obrigatorios": dados_obrigatorios or ["preco_atual", "cadeia_real", "liquidez", "perda_maxima"],
        "alertas": alertas or ["Sugestão gráfica; não representa ordem."],
    }


STRATEGY_CATALOG = [
    _strategy("long_call", "call comprada", "direcional", ["alta_forte"], "altista", "simples", delta_alvo_padrao="0,50 a 0,70", quando_usar="alta forte com catalisador e volatilidade aceitável", quando_evitar="lateralidade sem catalisador ou prêmio excessivo"),
    _strategy("long_put", "put comprada", "direcional", ["queda_forte"], "baixista", "simples", delta_alvo_padrao="-0,50 a -0,70", quando_usar="queda forte com continuação confirmada", quando_evitar="lateralidade sem catalisador ou prêmio excessivo"),
    _strategy("call_debit_spread", "call debit spread", "trava", ["alta_forte", "alta_moderada"], "altista", "intermediária", delta_alvo_padrao="0,40 a 0,60 na ponta comprada", quando_usar="alta com alvo definido", quando_evitar="alvo gráfico ausente ou débito excessivo"),
    _strategy("put_debit_spread", "put debit spread", "trava", ["queda_forte", "queda_moderada"], "baixista", "intermediária", delta_alvo_padrao="-0,40 a -0,60 na ponta comprada", quando_usar="queda com alvo definido", quando_evitar="alvo gráfico ausente ou débito excessivo"),
    _strategy("bull_put_spread", "bull put spread", "trava", ["alta_moderada", "alta_forte"], "altista", "intermediária", exige_caixa=True, delta_alvo_padrao="0,20 a 0,35 em módulo na ponta vendida", quando_usar="suporte altista claro e crédito suficiente", quando_evitar="suporte frágil ou perda máxima ausente"),
    _strategy("bear_call_spread", "bear call spread", "trava", ["queda_moderada"], "baixista", "intermediária", exige_caixa=True, delta_alvo_padrao="0,20 a 0,35 na ponta vendida", quando_usar="resistência clara em queda moderada", quando_evitar="resistência rompida ou perda máxima ausente"),
    _strategy("covered_call", "venda coberta", "renda_protecao", ["lateral", "alta_moderada"], "neutra_altista", "intermediária", exige_ativo=True, delta_alvo_padrao="0,20 a 0,35 na call vendida", quando_usar="usuário possui o ativo e aceita limitar a alta", quando_evitar="usuário não possui o ativo ou espera alta forte", dados_obrigatorios=["preco_atual", "posse_ativo", "cadeia_real", "liquidez", "perda_maxima"]),
    _strategy("cash_secured_put", "venda de put com caixa", "renda_protecao", ["alta_moderada"], "neutra_altista", "intermediária", exige_caixa=True, delta_alvo_padrao="-0,20 a -0,35 na put vendida", quando_usar="aceita adquirir o ativo abaixo do preço atual", quando_evitar="caixa ou suporte não confirmados", dados_obrigatorios=["preco_atual", "caixa_disponivel", "suporte", "cadeia_real", "liquidez", "perda_maxima"]),
    _strategy("protective_put", "protective put", "renda_protecao", ["alta_moderada", "queda_moderada"], "protecao", "intermediária", exige_ativo=True, delta_alvo_padrao="-0,30 a -0,50 na put comprada", quando_usar="proteger posição existente", quando_evitar="usuário não possui o ativo", dados_obrigatorios=["preco_atual", "posse_ativo", "cadeia_real", "liquidez", "perda_maxima"]),
    _strategy("collar", "collar", "renda_protecao", ["lateral", "alta_moderada"], "protecao", "avançada", exige_ativo=True, delta_alvo_padrao="put -0,30 a -0,50 e call 0,20 a 0,35", quando_usar="proteger ativo aceitando teto de ganho", quando_evitar="usuário não possui o ativo", dados_obrigatorios=["preco_atual", "posse_ativo", "cadeia_real", "liquidez", "perda_maxima"]),
    _strategy("iron_condor", "iron condor", "lateralidade", ["lateral"], "neutra", "avançada", exige_caixa=True, delta_alvo_padrao="0,15 a 0,25 em módulo nas pontas vendidas", quando_usar="range claro com prêmio suficiente", quando_evitar="suporte ou resistência ausentes, rompimento ou prêmio insuficiente", dados_obrigatorios=["preco_atual", "suporte", "resistencia", "cadeia_real", "premio", "liquidez", "spread", "break_even_inferior", "break_even_superior", "perda_maxima"]),
    _strategy("iron_butterfly", "iron butterfly", "lateralidade", ["lateral"], "neutra", "avançada", exige_caixa=True, delta_alvo_padrao="próximo de 0,50 em módulo no miolo", quando_usar="expectativa de permanência próxima ao centro do range", quando_evitar="movimento direcional ou range mal definido", dados_obrigatorios=["preco_atual", "suporte", "resistencia", "cadeia_real", "premio", "liquidez", "spread", "break_evens", "perda_maxima"]),
    _strategy("call_butterfly", "call butterfly", "lateralidade", ["lateral"], "neutra", "avançada", delta_alvo_padrao="definido após seleção dos strikes", quando_usar="alvo central e range bem definidos", quando_evitar="rompimento confirmado ou strikes sem liquidez"),
    _strategy("put_butterfly", "put butterfly", "lateralidade", ["lateral"], "neutra", "avançada", delta_alvo_padrao="definido após seleção dos strikes", quando_usar="alvo central e range bem definidos", quando_evitar="rompimento confirmado ou strikes sem liquidez"),
    _strategy("calendar_spread", "calendar", "lateralidade", ["lateral"], "neutra", "avançada", delta_alvo_padrao="próximo de 0,50 em módulo", vencimento_ideal="dois vencimentos; validar inclinação temporal", quando_usar="lateralidade com estrutura temporal favorável", quando_evitar="curva de volatilidade ou liquidez indisponível", dados_obrigatorios=["preco_atual", "cadeia_real", "dois_vencimentos", "volatilidade_implicita", "liquidez", "perda_maxima"]),
    _strategy("long_straddle", "straddle comprado", "volatilidade_evento", ["compressao"], "bidirecional", "avançada", delta_alvo_padrao="call e put próximas de 0,50 em módulo", quando_usar="compressão com evento ou catalisador", quando_evitar="custo alto ou ausência de catalisador", dados_obrigatorios=["preco_atual", "cadeia_real", "catalisador", "volatilidade_implicita", "custo", "break_evens", "perda_maxima"]),
    _strategy("long_strangle", "strangle comprado", "volatilidade_evento", ["compressao"], "bidirecional", "avançada", delta_alvo_padrao="0,30 a 0,40 em módulo", quando_usar="compressão com expectativa de movimento amplo", quando_evitar="custo alto ou ausência de catalisador", dados_obrigatorios=["preco_atual", "cadeia_real", "catalisador", "volatilidade_implicita", "custo", "break_evens", "perda_maxima"]),
    _strategy("short_straddle_travado", "straddle vendido travado", "lateralidade", ["lateral"], "neutra", "avançada", exige_caixa=True, delta_alvo_padrao="próximo de 0,50 em módulo nas opções vendidas", quando_usar="lateralidade forte, volatilidade cara e proteções compradas", quando_evitar="evento binário, proteção ausente ou perda máxima indefinida", alertas=["Somente versão travada; venda descoberta é rejeitada."]),
    _strategy("short_strangle_travado", "strangle vendido travado", "lateralidade", ["lateral"], "neutra", "avançada", exige_caixa=True, delta_alvo_padrao="0,20 a 0,35 em módulo nas opções vendidas", quando_usar="lateralidade ampla, volatilidade cara e range claro", quando_evitar="tendência forte, evento binário ou proteção ausente", alertas=["Somente versão travada; venda descoberta é rejeitada."]),
    _strategy("backspread_call", "backspread de call", "volatilidade_evento", ["compressao", "alta_forte"], "altista_volatilidade", "avançada", delta_alvo_padrao="definido após proporção e strikes", quando_usar="expansão altista esperada com risco travado", quando_evitar="risco ou proporção não calculados"),
    _strategy("backspread_put", "backspread de put", "volatilidade_evento", ["compressao", "queda_forte"], "baixista_volatilidade", "avançada", delta_alvo_padrao="definido após proporção e strikes", quando_usar="expansão baixista esperada com risco travado", quando_evitar="risco ou proporção não calculados"),
    _strategy("diagonal_spread", "diagonal spread", "avancada", ["alta_moderada", "queda_moderada", "lateral"], "variável", "avançada", delta_alvo_padrao="definido após pernas e vencimentos", vencimento_ideal="dois vencimentos; validar inclinação temporal", quando_usar="direção moderada com estrutura temporal", quando_evitar="tese indefinida ou curva temporal ausente", dados_obrigatorios=["preco_atual", "cadeia_real", "dois_vencimentos", "volatilidade_implicita", "liquidez", "perda_maxima"]),
    _strategy("ratio_spread_travado", "ratio spread travado", "avancada", ["alta_forte", "queda_forte", "compressao"], "variável", "avançada", delta_alvo_padrao="definido após proporção e strikes", quando_usar="movimento amplo com risco completamente travado", quando_evitar="qualquer risco descoberto ou perda máxima ausente", alertas=["Somente versão travada; venda descoberta é rejeitada."]),
    _strategy("synthetic_long_stock", "synthetic long stock", "avancada", ["alta_forte", "alta_moderada"], "altista", "avançada", exige_caixa=True, delta_alvo_padrao="delta líquido próximo de +1, sujeito à cadeia", quando_usar="replicar compra do ativo apenas em estudo avançado", quando_evitar="caixa ou margem insuficientes, risco de exercício ou perda elevada", alertas=["Não recomendar para pequeno capital sem validação completa."]),
    _strategy("synthetic_short_stock", "synthetic short stock", "avancada", [], "baixista", "avançada", exige_caixa=True, risco_definido=False, delta_alvo_padrao="delta líquido próximo de -1, sujeito à cadeia", quando_usar="somente estudo teórico avançado", quando_evitar="risco elevado, chamada de margem e call descoberta", alertas=["Rejeitada por padrão; contém venda de call descoberta."]),
]


def _details(
    explicacao_curta: str,
    pernas: list[str],
    tipo: str,
    tese_ideal: str,
    calculos_obrigatorios: list[str],
    *,
    ganho_maximo_existe: bool = True,
    exige_volatilidade: bool = False,
    exige_gregas: bool = False,
    status_padrao_sem_cadeia: str = "pendente_validacao_opcoes",
) -> dict[str, Any]:
    return {
        "explicacao_curta": explicacao_curta,
        "pernas": pernas,
        "tipo": tipo,
        "tese_ideal": tese_ideal,
        "ganho_maximo_existe": ganho_maximo_existe,
        "exige_volatilidade": exige_volatilidade,
        "exige_gregas": exige_gregas,
        "calculos_obrigatorios": calculos_obrigatorios,
        "status_padrao_sem_cadeia": status_padrao_sem_cadeia,
    }


STRATEGY_DETAILS = {
    "long_call": _details("Compra de call para capturar alta com perda limitada ao prêmio.", ["comprar call"], "direcional", "alta forte, rompimento confirmado ou catalisador", ["custo", "perda máxima", "break-even", "movimento necessário", "theta", "delta"], ganho_maximo_existe=False, exige_volatilidade=True, exige_gregas=True),
    "long_put": _details("Compra de put para capturar queda com perda limitada ao prêmio.", ["comprar put"], "direcional", "queda forte, perda de suporte ou proteção especulativa", ["custo", "perda máxima", "break-even", "movimento necessário", "theta", "delta"], exige_volatilidade=True, exige_gregas=True),
    "call_debit_spread": _details("Trava de alta com débito e risco definidos.", ["comprar call de strike menor", "vender call de strike maior"], "direcional", "alta moderada com alvo técnico definido", ["custo líquido", "perda máxima", "ganho máximo", "break-even", "retorno sobre risco"]),
    "put_debit_spread": _details("Trava de baixa com débito e risco definidos.", ["comprar put de strike maior", "vender put de strike menor"], "direcional", "queda moderada com alvo técnico definido", ["custo líquido", "perda máxima", "ganho máximo", "break-even"]),
    "bull_put_spread": _details("Trava de crédito neutra ou altista protegida por put comprada.", ["vender put de strike maior", "comprar put de strike menor"], "renda", "ativo acima de suporte com prêmio suficiente", ["crédito recebido", "perda máxima", "ganho máximo", "break-even", "margem"]),
    "bear_call_spread": _details("Trava de crédito neutra ou baixista protegida por call comprada.", ["vender call de strike menor", "comprar call de strike maior"], "renda", "ativo perto da resistência com prêmio suficiente", ["crédito recebido", "perda máxima", "ganho máximo", "break-even", "margem"]),
    "covered_call": _details("Venda de call coberta por ações já possuídas.", ["ter o ativo", "vender call acima do preço atual"], "renda", "ativo em carteira, lateral ou perto da resistência", ["prêmio", "retorno do prêmio", "preço efetivo de venda", "ganho máximo", "break-even"]),
    "cash_secured_put": _details("Venda de put com caixa reservado para eventual exercício.", ["vender put", "manter caixa para comprar o ativo se exercido"], "renda", "desejo de comprar o ativo abaixo ou perto do suporte", ["prêmio", "preço efetivo de compra", "break-even", "garantia necessária", "perda em queda forte"]),
    "protective_put": _details("Put comprada para estabelecer piso de proteção de uma posição em ações.", ["ter o ativo", "comprar put de proteção"], "proteção", "proteção de carteira ou ação específica", ["custo da proteção", "piso de proteção", "perda máxima protegida", "impacto no retorno"]),
    "collar": _details("Proteção com put financiada total ou parcialmente por call vendida.", ["ter o ativo", "comprar put abaixo", "vender call acima"], "proteção", "limitar queda aceitando teto para a alta", ["custo líquido", "piso", "teto", "perda máxima", "ganho máximo", "break-even"]),
    "iron_condor": _details("Duas travas de crédito delimitam uma faixa de lucro em mercado lateral.", ["vender put travada abaixo do suporte", "vender call travada acima da resistência"], "lateralidade", "suporte e resistência claros com volatilidade interessante", ["crédito recebido", "perda máxima", "ganho máximo", "break-even inferior", "break-even superior", "faixa de lucro"], exige_volatilidade=True),
    "iron_butterfly": _details("Venda de call e put centrais com proteções compradas nas pontas.", ["vender call e put no centro", "comprar proteção nas pontas"], "lateralidade", "ativo parado perto de preço específico e volatilidade alta", ["crédito", "perda máxima", "ganho máximo", "break-evens", "faixa ideal"], exige_volatilidade=True),
    "call_butterfly": _details("Butterfly com calls para buscar concentração perto de um alvo no vencimento.", ["comprar call baixa", "vender duas calls no meio", "comprar call alta"], "lateralidade", "ativo perto de alvo específico no vencimento", ["custo", "perda máxima", "ganho máximo", "ponto de maior ganho", "break-evens"]),
    "put_butterfly": _details("Butterfly com puts para buscar queda até uma região-alvo e estabilização.", ["comprar put alta", "vender duas puts no meio", "comprar put baixa"], "lateralidade", "queda até região-alvo com estabilização", ["custo", "perda máxima", "ganho máximo", "ponto de maior ganho", "break-evens"]),
    "calendar_spread": _details("Compra opção longa e vende opção curta em strike igual ou próximo.", ["comprar opção de vencimento mais longo", "vender opção de vencimento curto no mesmo strike ou próximo"], "lateralidade", "movimento lento perto do strike e diferença de theta", ["custo", "risco", "efeito do tempo", "efeito da volatilidade", "plano para vencimento curto"], exige_volatilidade=True, exige_gregas=True),
    "diagonal_spread": _details("Combina strikes e vencimentos diferentes para direção moderada e geração de prêmio.", ["comprar opção longa em um strike", "vender opção curta em outro strike"], "avançada", "tese moderada com plano de rolagem", ["custo líquido", "risco", "ganho potencial", "efeito do theta", "efeito da volatilidade"], exige_volatilidade=True, exige_gregas=True),
    "long_straddle": _details("Compra call e put próximas do preço para capturar movimento forte em qualquer direção.", ["comprar call no mesmo strike ou próximo do preço", "comprar put no mesmo strike ou próximo do preço"], "volatilidade", "movimento forte com direção incerta e evento relevante", ["custo total", "perda máxima", "break-even superior", "break-even inferior", "movimento necessário"], exige_volatilidade=True, exige_gregas=True),
    "long_strangle": _details("Compra call e put OTM para capturar movimento amplo com custo menor.", ["comprar call OTM", "comprar put OTM"], "volatilidade", "movimento forte com strikes ainda alcançáveis", ["custo total", "perda máxima", "break-even superior", "break-even inferior", "movimento necessário"], exige_volatilidade=True, exige_gregas=True),
    "short_straddle_travado": _details("Venda central de call e put com proteções que limitam o risco.", ["vender call e put no centro", "comprar proteções nas pontas"], "lateralidade", "lateralidade forte e volatilidade cara com risco travado", ["crédito", "perda máxima", "ganho máximo", "break-evens"], exige_volatilidade=True, exige_gregas=True),
    "short_strangle_travado": _details("Venda afastada de call e put com proteções compradas nas pontas.", ["vender call acima", "vender put abaixo", "comprar proteções nas pontas"], "lateralidade", "lateralidade ampla com suporte e resistência claros", ["crédito", "perda máxima", "ganho máximo", "break-evens", "faixa de lucro"], exige_volatilidade=True, exige_gregas=True),
    "backspread_call": _details("Vende uma call e compra maior quantidade de calls acima para alta explosiva.", ["vender call mais baixa", "comprar mais calls em strike superior"], "avançada", "alta explosiva com risco controlado", ["custo ou crédito", "zona de perda", "ganho potencial", "break-even"], ganho_maximo_existe=False, exige_volatilidade=True, exige_gregas=True),
    "backspread_put": _details("Vende uma put e compra maior quantidade de puts abaixo para queda explosiva.", ["vender put mais alta", "comprar mais puts em strike inferior"], "avançada", "queda explosiva com risco controlado", ["custo ou crédito", "zona de perda", "ganho potencial", "break-even"], exige_volatilidade=True, exige_gregas=True),
    "ratio_spread_travado": _details("Ratio spread com proteção adicional para eliminar risco descoberto.", ["comprar uma opção", "vender quantidade maior em outro strike", "comprar proteção adicional para limitar risco"], "avançada", "tese moderada com risco integralmente definido", ["custo ou crédito", "perda máxima", "ganho máximo", "zona de risco"], exige_gregas=True),
    "synthetic_long_stock": _details("Call comprada e put vendida replicam economicamente a compra do ativo.", ["comprar call", "vender put no mesmo strike"], "avançada", "replicação teórica da compra do ativo com caixa e margem", ["custo ou crédito", "margem", "break-even", "perda máxima", "risco de exercício"], ganho_maximo_existe=False, exige_gregas=True),
    "synthetic_short_stock": _details("Put comprada e call vendida replicam economicamente a venda do ativo.", ["comprar put", "vender call no mesmo strike"], "avançada", "somente estudo teórico", ["custo ou crédito", "margem", "break-even", "perda potencial", "risco de exercício"], ganho_maximo_existe=True, exige_gregas=True, status_padrao_sem_cadeia="rejeitada"),
}


for _entry in STRATEGY_CATALOG:
    _entry.update(STRATEGY_DETAILS[_entry["id"]])
    _entry["delta_alvo"] = _entry["delta_alvo_padrao"]
    _entry["manual_validation_required"] = True
    _entry["objective_classification_required"] = True


def get_strategy_catalog() -> list[dict[str, Any]]:
    return [dict(item) for item in STRATEGY_CATALOG]
