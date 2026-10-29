"""Personas de teste e demonstração.

Cada persona traz um perfil completo e as trilhas que se espera encontrar
entre as três primeiras (``esperado_top3``). A interface usa estas personas
no menu "Perfis de demonstração" e os testes automatizados as validam.
"""
from __future__ import annotations


def _r(logica, matematica, design, dados, infra, seguranca, automacao, testes, mobile, negocios):
    return {"logica": logica, "matematica": matematica, "design": design, "dados": dados,
            "infra": infra, "seguranca": seguranca, "automacao": automacao, "testes": testes,
            "mobile": mobile, "negocios": negocios}


PERSONAS = {
    "analitica": {
        "nome": "Perfil analítico",
        "descricao": "Gosta de matemática, estatística e dados; conhece Python e bibliotecas de análise.",
        "perfil": {"nivel": "intermediario", "experiencias": ["academicos", "pessoais"],
                   "ferramentas": ["python", "data_libs", "estatistica", "sql"],
                   "objetivos": ["gerar_insights"], "preferencias": ["experimentos"],
                   "respostas": _r(4, 5, 2, 5, 2, 2, 3, 2, 1, 3)},
        "esperado_primeiro": "data_science",
        "esperado_top3": ["data_science"],
    },
    "visual": {
        "nome": "Perfil visual",
        "descricao": "Forte interesse em design e experiência do usuário; conhece HTML, CSS e JavaScript.",
        "perfil": {"nivel": "basico", "experiencias": ["cursos"],
                   "ferramentas": ["html_css", "javascript", "figma"],
                   "objetivos": ["criar_interfaces"], "preferencias": ["visual"],
                   "respostas": _r(3, 2, 5, 2, 1, 1, 2, 3, 3, 4)},
        "esperado_primeiro": "frontend",
        "esperado_top3": ["frontend"],
    },
    "infra_seguranca": {
        "nome": "Perfil infraestrutura/segurança",
        "descricao": "Gosta de redes, Linux e proteção de sistemas.",
        "perfil": {"nivel": "basico", "experiencias": ["cursos", "pessoais"],
                   "ferramentas": ["linux", "redes", "seg_ferramentas"],
                   "objetivos": ["proteger"], "preferencias": ["investigacao"],
                   "respostas": _r(3, 2, 1, 2, 5, 5, 4, 2, 1, 2)},
        "esperado_primeiro": "security",
        "esperado_top3": ["security", "devops", "cloud"],
    },
    "negocios_produto": {
        "nome": "Perfil negócios/produto",
        "descricao": "Interessa-se por usuários, planejamento e priorização; pouca programação.",
        "perfil": {"nivel": "iniciante", "experiencias": ["academicos"],
                   "ferramentas": ["agil"],
                   "objetivos": ["definir_produtos"], "preferencias": ["pessoas"],
                   "respostas": _r(2, 2, 4, 3, 1, 1, 2, 3, 2, 5)},
        "esperado_primeiro": "product",
        "esperado_top3": ["product"],
    },
    "ambigua_dados_programacao": {
        "nome": "Perfil ambíguo (dados + programação)",
        "descricao": "Afinidade alta tanto por dados quanto por programação e automação; objetivo ainda indefinido.",
        "perfil": {"nivel": "intermediario", "experiencias": ["pessoais"],
                   "ferramentas": ["python", "sql"],
                   "objetivos": ["explorando"], "preferencias": [],
                   "respostas": _r(5, 4, 2, 5, 3, 2, 4, 3, 1, 2)},
        "esperado_primeiro": None,
        "esperado_top3": ["data_science", "data_engineering", "backend"],
    },
    "iniciante": {
        "nome": "Perfil iniciante",
        "descricao": "Está começando, não conhece ferramentas e tem respostas moderadas.",
        "perfil": {"nivel": "iniciante", "experiencias": ["nenhuma"],
                   "ferramentas": [], "objetivos": ["explorando"], "preferencias": [],
                   "respostas": _r(3, 3, 4, 3, 3, 3, 3, 3, 3, 4)},
        "esperado_primeiro": None,
        "esperado_top3": [],
    },
    "design_mobile": {
        "nome": "Perfil design + mobile",
        "descricao": "Gosta de desenhar interfaces e de criar aplicativos para celular.",
        "perfil": {"nivel": "basico", "experiencias": ["cursos"],
                   "ferramentas": ["figma", "mobile_framework"],
                   "objetivos": ["criar_apps"], "preferencias": ["visual", "codigo"],
                   "respostas": _r(4, 2, 5, 2, 1, 2, 2, 3, 5, 3)},
        "esperado_primeiro": None,
        "esperado_top3": ["mobile", "frontend"],
    },
    "equilibrada": {
        "nome": "Perfil equilibrado (todas as respostas moderadas)",
        "descricao": "Responde 3 em tudo e não declara ferramentas nem objetivos: o modelo não deve forçar um vencedor.",
        "perfil": {"nivel": "basico", "experiencias": [], "ferramentas": [],
                   "objetivos": [], "preferencias": [],
                   "respostas": _r(3, 3, 3, 3, 3, 3, 3, 3, 3, 3)},
        "esperado_primeiro": None,
        "esperado_top3": [],
    },
}
