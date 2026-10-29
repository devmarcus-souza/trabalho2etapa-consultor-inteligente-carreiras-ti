"""Geração do roadmap personalizado a partir da carreira e das lacunas."""
from __future__ import annotations

TITULOS_ETAPAS = (
    ("fundamentos", "1. Fundamentos"),
    ("ferramentas_prioritarias", "2. Tecnologias e ferramentas prioritárias"),
    ("competencias_intermediarias", "3. Competências intermediárias"),
    ("praticas_exercicios", "4. Práticas e exercícios"),
    ("portfolio", "5. Projeto de portfólio"),
    ("oportunidades_junior", "6. Próximos passos para oportunidades de nível Júnior"),
)


def _item(texto, tipo):
    """tipo: 'base' (conteúdo da trilha), 'lacuna' (personalizado) ou 'aprofundamento'."""
    return {"texto": texto, "tipo": tipo}


def gerar_roadmap(base: dict, carreira_id: str, analise: dict, perfil) -> dict:
    """Monta as etapas do plano, destacando o que vem das lacunas do usuário."""
    if carreira_id not in base["carreiras"]:
        raise ValueError(f"Carreira desconhecida: {carreira_id!r}")
    carreira = base["carreiras"][carreira_id]
    rm = carreira["roadmap"]
    iniciante = perfil.nivel in (None, "iniciante")

    essenciais = [l for l in analise["lacunas"] if l["prioridade"] == "essencial"]
    importantes = [l for l in analise["lacunas"] if l["prioridade"] == "importante"]

    etapas = []
    for chave, titulo in TITULOS_ETAPAS:
        itens, descricao = [], ""
        if chave == "fundamentos":
            descricao = ("Comece por aqui, na ordem apresentada." if iniciante else
                         "Revise rapidamente o que já domina e aprofunde apenas os pontos em que sentir insegurança.")
            itens = [_item(t, "base") for t in rm["fundamentos"]]
        elif chave == "ferramentas_prioritarias":
            descricao = "Ferramentas centrais da trilha, com foco nas lacunas essenciais identificadas."
            itens = [_item(t, "base") for t in rm["ferramentas_prioritarias"]]
            itens += [_item(f"Lacuna essencial — {l['nome']}: {l['descricao']}", "lacuna") for l in essenciais]
        elif chave == "competencias_intermediarias":
            descricao = "Competências que ampliam sua autonomia depois da base."
            itens = [_item(t, "base") for t in rm["competencias_intermediarias"]]
            itens += [_item(f"Lacuna importante — {l['nome']}: {l['descricao']}", "lacuna") for l in importantes]
        elif chave == "praticas_exercicios":
            descricao = "Pratique continuamente; aprender fazendo é o que sustenta o portfólio."
            itens = [_item(t, "base") for t in rm["praticas_exercicios"]]
            itens += [_item(f"Aprofundar o que você declarou ({d['nome']}): aplique em um projeto completo, "
                            "não apenas em exercícios isolados.", "aprofundamento") for d in analise["declarados"]]
        elif chave == "portfolio":
            projeto = carreira["projeto_portfolio"]
            descricao = projeto["descricao"]
            itens = [_item(f"Projeto sugerido: {projeto['titulo']}", "base")]
            itens += [_item(f"Entregável: {e}", "base") for e in projeto["entregaveis"]]
        elif chave == "oportunidades_junior":
            descricao = "Transforme o aprendizado em evidências visíveis para recrutadores. Não há garantia de contratação; isso depende do mercado e do seu histórico."
            itens = [_item(t, "base") for t in rm["oportunidades_junior"]]
        etapas.append({"chave": chave, "titulo": titulo, "descricao": descricao, "itens": itens})

    return {
        "carreira_id": carreira_id,
        "carreira_nome": carreira["nome"],
        "etapas": etapas,
        "certificacoes": carreira["certificacoes_opcionais"],
        "aviso_certificacoes": base["parametros"]["aviso_certificacoes"],
        "projeto": carreira["projeto_portfolio"],
    }
