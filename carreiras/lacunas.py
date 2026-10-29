"""Análise de lacunas de competências (Skill Gap Analysis) para o nível Júnior.

Distinção importante:
- "declarado": o usuário informou uma ferramenta ligada à competência. Isso NÃO
  é tratado como lacuna, mas o sistema recomenda aprofundar até nível de projeto.
- "presumida": o usuário não declarou nada ligado à competência. O sistema
  PRESUME que ela precisa ser desenvolvida (ele não consegue verificar o
  conhecimento real da pessoa).
"""
from __future__ import annotations

ORIGEM_DECLARADO = "declarado pelo usuário"
ORIGEM_PRESUMIDA = "presumida pelo sistema"


def analisar_lacunas(base: dict, carreira_id: str, perfil) -> dict:
    """Compara o perfil com as competências de nível Júnior da carreira."""
    if carreira_id not in base["carreiras"]:
        raise ValueError(f"Carreira desconhecida: {carreira_id!r}")
    carreira = base["carreiras"][carreira_id]
    nomes_ferr = {f["id"]: f["nome"] for f in base["ferramentas"]}
    declaradas = {f for f in (perfil.ferramentas or []) if f in nomes_ferr}
    niveis = {n["id"]: n for n in base["niveis_conhecimento"]}
    nivel = niveis.get(perfil.nivel)

    declarados, lacunas = [], []
    for comp in carreira["competencias_junior"]:
        coincidentes = [f for f in comp["ferramentas_relacionadas"] if f in declaradas]
        item = {"id": comp["id"], "nome": comp["nome"], "descricao": comp["descricao"],
                "prioridade": comp["prioridade"]}
        if coincidentes:
            item.update({
                "origem": ORIGEM_DECLARADO,
                "evidencia": [nomes_ferr[f] for f in coincidentes],
                "aprofundamento": ("Você declarou conhecer " + ", ".join(nomes_ferr[f] for f in coincidentes)
                                   + ". Isso não é uma lacuna, mas para o nível Júnior é preciso aplicar o "
                                     "conhecimento em um projeto completo, com testes e documentação."),
            })
            declarados.append(item)
        else:
            if comp["ferramentas_relacionadas"]:
                motivo = ("Você não declarou ferramentas ligadas a esta competência: "
                          + ", ".join(nomes_ferr[f] for f in comp["ferramentas_relacionadas"]) + ".")
            else:
                motivo = ("O sistema não tem como verificar esta competência a partir das ferramentas declaradas; "
                          "ela é presumida como ponto a desenvolver. Se você já a domina, ignore este item.")
            item.update({"origem": ORIGEM_PRESUMIDA, "motivo": motivo})
            lacunas.append(item)

    ordem = {"essencial": 0, "importante": 1}
    lacunas.sort(key=lambda x: ordem[x["prioridade"]])
    total = len(carreira["competencias_junior"])
    observacoes = []
    if nivel is not None and nivel["ordem"] == 0:
        observacoes.append("Como você se declarou iniciante, comece pelos fundamentos antes de avançar para as lacunas listadas.")
    elif nivel is not None and nivel["ordem"] >= 2 and lacunas:
        observacoes.append("Você indicou nível intermediário ou avançado: confirme se as lacunas presumidas realmente se aplicam ao seu caso.")
    if not declaradas:
        observacoes.append("Nenhuma ferramenta foi declarada; todas as competências foram tratadas como lacunas presumidas.")

    return {
        "carreira_id": carreira_id,
        "carreira_nome": carreira["nome"],
        "nivel_usuario": nivel["nome"] if nivel else "Não informado",
        "total_competencias": total,
        "declarados": declarados,
        "lacunas": lacunas,
        "cobertura_declarada_percentual": round(100 * len(declarados) / total, 1) if total else 0.0,
        "observacoes": observacoes,
    }
