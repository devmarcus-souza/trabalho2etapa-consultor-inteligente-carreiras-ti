"""Regras de inferência qualitativas (lidas de regras_carreiras.json).

Estas regras NÃO alteram a pontuação. Elas observam o perfil (respostas,
nível, ferramentas) e produzem sinais em linguagem natural, como
"perfil híbrido dados + programação", além de carreiras alternativas.
O cálculo numérico de compatibilidade fica em motor.py.
"""
from __future__ import annotations

from .base_conhecimento import OPERADORES, eh_numero


def avaliar_regras(base: dict, contexto: dict) -> list:
    """Devolve as regras cujas condições (todas) são verdadeiras para o contexto.

    ``contexto`` mapeia campos (ids de dimensões, 'nivel', 'num_ferramentas',
    'media_respostas', 'amplitude_respostas') para números. Campo ausente
    ou não numérico faz a condição ser falsa (regra não dispara).
    """
    acionadas = []
    for regra in base.get("regras_inferencia", []):
        satisfeita = True
        for cond in regra["condicoes"]:
            valor = contexto.get(cond["campo"])
            if not eh_numero(valor) or not OPERADORES[cond["operador"]](valor, cond["valor"]):
                satisfeita = False
                break
        if satisfeita:
            acionadas.append({
                "id": regra["id"],
                "nome": regra.get("nome", regra["id"]),
                "mensagem": regra["mensagem"],
                "carreiras": list(regra["carreiras"]),
            })
    return acionadas
