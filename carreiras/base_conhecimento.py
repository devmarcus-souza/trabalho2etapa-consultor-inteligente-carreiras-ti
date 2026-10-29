"""Carregamento e validação da base de conhecimento (regras_carreiras.json).

A base fica fora do código Python: para ajustar pesos, textos ou incluir uma
nova carreira basta editar o JSON. Este módulo garante que o arquivo está
completo e coerente antes de o motor de pontuação usá-lo.
"""
from __future__ import annotations

import json
import math
import operator
from pathlib import Path

CAMINHO_PADRAO = Path(__file__).resolve().parent.parent / "regras_carreiras.json"

# Identificadores das dez trilhas obrigatórias (os mesmos usados na Etapa 1).
CARREIRAS_OBRIGATORIAS = (
    "backend", "frontend", "data_science", "data_engineering", "security",
    "devops", "cloud", "mobile", "qa", "product",
)

ETAPAS_ROADMAP = (
    "fundamentos", "ferramentas_prioritarias", "competencias_intermediarias",
    "praticas_exercicios", "oportunidades_junior",
)

PRIORIDADES = ("essencial", "importante")

OPERADORES = {
    ">=": operator.ge, "<=": operator.le, "==": operator.eq,
    "!=": operator.ne, ">": operator.gt, "<": operator.lt,
}

# Campos extras (além dos ids das dimensões) que as regras de inferência podem usar.
CAMPOS_EXTRAS_REGRAS = ("nivel", "num_ferramentas", "media_respostas", "amplitude_respostas")

CHAVES_RAIZ = (
    "parametros", "dimensoes", "niveis_conhecimento", "experiencias",
    "ferramentas", "objetivos", "preferencias", "regras_inferencia", "carreiras",
)

PARAMETROS_PESOS_COMPLEMENTARES = (
    "peso_afinidade", "peso_ferramentas", "peso_objetivos", "peso_preferencias",
)


class BaseConhecimentoError(Exception):
    """Erro ao carregar ou validar a base. A lista completa fica em ``erros``."""

    def __init__(self, erros):
        self.erros = list(erros)
        super().__init__("; ".join(self.erros))


def eh_numero(valor) -> bool:
    """True para int/float finitos (bool não conta como número)."""
    return (isinstance(valor, (int, float)) and not isinstance(valor, bool)
            and math.isfinite(valor))


def normalizar_pesos(pesos: dict) -> dict:
    """Divide cada peso pela soma, de modo que os pesos somem 1."""
    total = sum(pesos.values())
    if total <= 0:
        raise ValueError("A soma dos pesos precisa ser maior que zero.")
    return {chave: valor / total for chave, valor in pesos.items()}


def campos_regras(base: dict) -> set:
    """Campos que podem aparecer nas condições das regras de inferência."""
    ids = {d.get("id") for d in base.get("dimensoes", []) if isinstance(d, dict)}
    return ids | set(CAMPOS_EXTRAS_REGRAS)


def _texto_ok(valor) -> bool:
    return isinstance(valor, str) and bool(valor.strip())


def _lista_textos_ok(valor) -> bool:
    return (isinstance(valor, list) and len(valor) > 0
            and all(_texto_ok(item) for item in valor))


def _ids_unicos(itens, rotulo, erros):
    ids = []
    if not isinstance(itens, list) or not itens:
        erros.append(f"'{rotulo}' deve ser uma lista não vazia.")
        return ids
    for pos, item in enumerate(itens):
        if not isinstance(item, dict) or not _texto_ok(item.get("id")):
            erros.append(f"'{rotulo}' item {pos}: campo 'id' ausente ou inválido.")
            continue
        if item["id"] in ids:
            erros.append(f"'{rotulo}': id duplicado '{item['id']}'.")
        ids.append(item["id"])
        if not _texto_ok(item.get("nome")):
            erros.append(f"'{rotulo}' item '{item['id']}': campo 'nome' ausente.")
    return ids


def _validar_parametros(base, erros):
    parametros = base.get("parametros")
    if not isinstance(parametros, dict):
        erros.append("'parametros' deve ser um objeto.")
        return
    soma = 0.0
    pesos_ok = True
    for chave in PARAMETROS_PESOS_COMPLEMENTARES:
        valor = parametros.get(chave)
        if not eh_numero(valor) or not 0 <= valor <= 1:
            erros.append(f"parametros.{chave} deve ser um número entre 0 e 1.")
            pesos_ok = False
        else:
            soma += valor
    if pesos_ok and abs(soma - 1.0) > 0.001:
        erros.append(f"Os pesos dos fatores (afinidade, ferramentas, objetivos, preferências) "
                     f"devem somar 1, mas somam {soma:.3f}.")
    cap = parametros.get("peso_maximo_por_dimensao")
    if not eh_numero(cap) or not 0 < cap <= 1:
        erros.append("parametros.peso_maximo_por_dimensao deve ser um número entre 0 e 1.")
    neutra = parametros.get("resposta_neutra")
    if not eh_numero(neutra) or not 1 <= neutra <= 5:
        erros.append("parametros.resposta_neutra deve ser um número entre 1 e 5.")
    minimo = parametros.get("minimo_dimensoes_respondidas")
    n_dim = len(base.get("dimensoes", [])) if isinstance(base.get("dimensoes"), list) else 0
    if not isinstance(minimo, int) or isinstance(minimo, bool) or not 1 <= minimo <= max(n_dim, 1):
        erros.append("parametros.minimo_dimensoes_respondidas deve ser inteiro entre 1 e o número de dimensões.")
    for chave in ("margem_proximidade", "limite_clareza", "amplitude_perfil_equilibrado"):
        if not eh_numero(parametros.get(chave)) or parametros[chave] < 0:
            erros.append(f"parametros.{chave} deve ser um número maior ou igual a 0.")
    casas = parametros.get("casas_decimais")
    if not isinstance(casas, int) or isinstance(casas, bool) or not 0 <= casas <= 4:
        erros.append("parametros.casas_decimais deve ser inteiro entre 0 e 4.")
    if not _texto_ok(parametros.get("aviso_certificacoes")):
        erros.append("parametros.aviso_certificacoes é obrigatório.")


def _validar_fatores(base, chave, ids_carreiras, erros):
    ids = _ids_unicos(base.get(chave), chave, erros)
    itens = base.get(chave)
    for item in itens if isinstance(itens, list) else []:
        if not isinstance(item, dict):
            continue
        rel = item.get("relevancia")
        rotulo = f"{chave}.{item.get('id')}"
        if not isinstance(rel, dict):
            erros.append(f"{rotulo}: 'relevancia' deve ser um objeto (pode ser vazio).")
            continue
        for carreira, valor in rel.items():
            if carreira not in ids_carreiras:
                erros.append(f"{rotulo}: carreira desconhecida '{carreira}' em 'relevancia'.")
            if not eh_numero(valor) or not 0 <= valor <= 1:
                erros.append(f"{rotulo}: relevância de '{carreira}' deve estar entre 0 e 1.")
    return ids


def _validar_carreira(cid, carreira, ids_dim, ids_ferramentas, cap, erros):
    p = f"carreiras.{cid}"
    if not isinstance(carreira, dict):
        erros.append(f"{p}: deve ser um objeto.")
        return
    for campo in ("nome", "descricao"):
        if not _texto_ok(carreira.get(campo)):
            erros.append(f"{p}: campo obrigatório '{campo}' ausente ou vazio.")
    if not _lista_textos_ok(carreira.get("caracteristicas")):
        erros.append(f"{p}: 'caracteristicas' deve ser uma lista de textos não vazia.")
    if not _lista_textos_ok(carreira.get("conhecimentos_recomendados")):
        erros.append(f"{p}: 'conhecimentos_recomendados' deve ser uma lista de textos não vazia.")

    pesos = carreira.get("pesos")
    if not isinstance(pesos, dict):
        erros.append(f"{p}: 'pesos' deve ser um objeto.")
    else:
        pesos_ok = True
        for dim in ids_dim:
            if dim not in pesos:
                erros.append(f"{p}.pesos: falta a dimensão '{dim}'.")
                pesos_ok = False
        for dim, valor in pesos.items():
            if dim not in ids_dim:
                erros.append(f"{p}.pesos: dimensão desconhecida '{dim}'.")
                pesos_ok = False
            elif not eh_numero(valor) or not 0 <= valor <= 10:
                erros.append(f"{p}.pesos.{dim}: deve ser um número entre 0 e 10.")
                pesos_ok = False
        if pesos_ok:
            total = sum(pesos.values())
            if total <= 0:
                erros.append(f"{p}.pesos: a soma dos pesos deve ser maior que zero.")
            elif eh_numero(cap) and max(pesos.values()) / total > cap + 1e-9:
                erros.append(f"{p}.pesos: uma única dimensão tem {max(pesos.values())/total:.0%} do peso total, "
                             f"acima do limite de {cap:.0%}.")

    comps = carreira.get("competencias_junior")
    if not isinstance(comps, list) or not comps:
        erros.append(f"{p}: 'competencias_junior' deve ser uma lista não vazia.")
    else:
        ids_comp = []
        for comp in comps:
            if not isinstance(comp, dict):
                erros.append(f"{p}.competencias_junior: item inválido.")
                continue
            id_comp = comp.get("id")
            if not _texto_ok(id_comp):
                erros.append(f"{p}.competencias_junior: item sem 'id'.")
                continue
            if id_comp in ids_comp:
                erros.append(f"{p}.competencias_junior: id duplicado '{id_comp}'.")
            ids_comp.append(id_comp)
            for campo in ("nome", "descricao"):
                if not _texto_ok(comp.get(campo)):
                    erros.append(f"{p}.competencias_junior.{id_comp}: campo '{campo}' ausente.")
            if comp.get("prioridade") not in PRIORIDADES:
                erros.append(f"{p}.competencias_junior.{id_comp}: 'prioridade' deve ser uma de {PRIORIDADES}.")
            rel = comp.get("ferramentas_relacionadas")
            if not isinstance(rel, list):
                erros.append(f"{p}.competencias_junior.{id_comp}: 'ferramentas_relacionadas' deve ser uma lista.")
            else:
                for f in rel:
                    if f not in ids_ferramentas:
                        erros.append(f"{p}.competencias_junior.{id_comp}: ferramenta desconhecida '{f}'.")

    roadmap = carreira.get("roadmap")
    if not isinstance(roadmap, dict):
        erros.append(f"{p}: 'roadmap' deve ser um objeto.")
    else:
        for etapa in ETAPAS_ROADMAP:
            if not _lista_textos_ok(roadmap.get(etapa)):
                erros.append(f"{p}.roadmap: etapa '{etapa}' ausente ou vazia.")

    certs = carreira.get("certificacoes_opcionais")
    if not isinstance(certs, list) or not certs:
        erros.append(f"{p}: 'certificacoes_opcionais' deve ser uma lista não vazia.")
    else:
        for cert in certs:
            if not isinstance(cert, dict) or not _texto_ok(cert.get("nome")) or not _texto_ok(cert.get("emissor")):
                erros.append(f"{p}.certificacoes_opcionais: cada item precisa de 'nome' e 'emissor'.")

    projeto = carreira.get("projeto_portfolio")
    if not isinstance(projeto, dict):
        erros.append(f"{p}: 'projeto_portfolio' deve ser um objeto.")
    else:
        for campo in ("titulo", "descricao"):
            if not _texto_ok(projeto.get(campo)):
                erros.append(f"{p}.projeto_portfolio: campo '{campo}' ausente.")
        if not _lista_textos_ok(projeto.get("entregaveis")):
            erros.append(f"{p}.projeto_portfolio: 'entregaveis' deve ser uma lista de textos não vazia.")


def _validar_regras(base, ids_carreiras, erros):
    regras = base.get("regras_inferencia")
    if not isinstance(regras, list):
        erros.append("'regras_inferencia' deve ser uma lista.")
        return
    campos = campos_regras(base)
    vistos = []
    for pos, regra in enumerate(regras):
        if not isinstance(regra, dict) or not _texto_ok(regra.get("id")):
            erros.append(f"regras_inferencia item {pos}: 'id' ausente ou inválido.")
            continue
        rid = regra["id"]
        if rid in vistos:
            erros.append(f"regras_inferencia: id duplicado '{rid}'.")
        vistos.append(rid)
        if not _texto_ok(regra.get("mensagem")):
            erros.append(f"regras_inferencia.{rid}: 'mensagem' ausente.")
        carreiras = regra.get("carreiras")
        if not isinstance(carreiras, list) or any(c not in ids_carreiras for c in carreiras):
            erros.append(f"regras_inferencia.{rid}: 'carreiras' deve ser uma lista de ids existentes.")
        condicoes = regra.get("condicoes")
        if not isinstance(condicoes, list) or not condicoes:
            erros.append(f"regras_inferencia.{rid}: 'condicoes' deve ser uma lista não vazia.")
            continue
        for cond in condicoes:
            if (not isinstance(cond, dict) or cond.get("campo") not in campos
                    or cond.get("operador") not in OPERADORES or not eh_numero(cond.get("valor"))):
                erros.append(f"regras_inferencia.{rid}: condição inválida {cond!r}.")


def validar_base(base) -> list:
    """Valida a estrutura da base e devolve a lista de problemas (vazia se OK)."""
    erros: list = []
    if not isinstance(base, dict):
        return ["O conteúdo do arquivo deve ser um objeto JSON."]
    for chave in CHAVES_RAIZ:
        if chave not in base:
            erros.append(f"Chave obrigatória ausente: '{chave}'.")
    if erros:
        return erros

    _validar_parametros(base, erros)
    ids_dim = _ids_unicos(base["dimensoes"], "dimensoes", erros)
    dims = base["dimensoes"]
    for dim in dims if isinstance(dims, list) else []:
        if isinstance(dim, dict) and not _texto_ok(dim.get("pergunta")):
            erros.append(f"dimensoes.{dim.get('id')}: campo 'pergunta' ausente.")

    niveis = base["niveis_conhecimento"]
    _ids_unicos(niveis, "niveis_conhecimento", erros)
    for nivel in niveis if isinstance(niveis, list) else []:
        if isinstance(nivel, dict) and (not isinstance(nivel.get("ordem"), int) or isinstance(nivel.get("ordem"), bool)):
            erros.append(f"niveis_conhecimento.{nivel.get('id')}: 'ordem' deve ser inteiro.")
    _ids_unicos(base["experiencias"], "experiencias", erros)

    carreiras = base["carreiras"]
    if not isinstance(carreiras, dict) or not carreiras:
        erros.append("'carreiras' deve ser um objeto não vazio.")
        return erros
    for obrigatoria in CARREIRAS_OBRIGATORIAS:
        if obrigatoria not in carreiras:
            erros.append(f"Carreira obrigatória ausente: '{obrigatoria}'.")
    ids_carreiras = set(carreiras)

    ids_ferr = set(_validar_fatores(base, "ferramentas", ids_carreiras, erros))
    _validar_fatores(base, "objetivos", ids_carreiras, erros)
    _validar_fatores(base, "preferencias", ids_carreiras, erros)

    cap = base["parametros"].get("peso_maximo_por_dimensao") if isinstance(base["parametros"], dict) else None
    for cid, carreira in carreiras.items():
        _validar_carreira(cid, carreira, ids_dim, ids_ferr, cap, erros)
    _validar_regras(base, ids_carreiras, erros)
    return erros


def carregar_base(caminho=None) -> dict:
    """Lê o JSON, valida e devolve a base. Lança BaseConhecimentoError se houver problemas."""
    caminho = Path(caminho) if caminho else CAMINHO_PADRAO
    if not caminho.is_file():
        raise BaseConhecimentoError([f"Arquivo da base de conhecimento não encontrado: {caminho}"])
    try:
        texto = caminho.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise BaseConhecimentoError([f"Não foi possível ler {caminho.name}: {exc}"]) from exc
    try:
        base = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise BaseConhecimentoError(
            [f"JSON inválido em {caminho.name} (linha {exc.lineno}, coluna {exc.colno}): {exc.msg}"]) from exc
    erros = validar_base(base)
    if erros:
        raise BaseConhecimentoError(erros)
    return base
