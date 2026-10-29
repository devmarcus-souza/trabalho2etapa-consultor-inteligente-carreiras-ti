"""Motor de pontuação ponderada de compatibilidade com carreiras de TI.

Fórmula (para cada carreira c):

    n_i   = (resposta_i - 1) / 4                       (normalização 1..5 -> 0..1)
    w_ci  = peso_ci / soma_j(peso_cj)                  (pesos normalizados, somam 1)
    A_c   = soma_i( w_ci * n_i )                       (afinidade, 0..1)
    T_c   = 1 - produto_t( 1 - r_tc )                  (ferramentas conhecidas, 0..1)
    O_c   = max_o( r_oc )                              (objetivos escolhidos, 0..1)
    P_c   = max_p( r_pc )                              (preferências de atuação, 0..1)

    S_c = 100 * (a*A_c + b*T_c + g*O_c + d*P_c)        com a+b+g+d = 1

Os parâmetros a, b, g, d ficam em regras_carreiras.json ("parametros").
O resultado S_c é uma ESTIMATIVA DE COMPATIBILIDADE produzida pelo modelo;
não é probabilidade de sucesso profissional.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .base_conhecimento import eh_numero, normalizar_pesos
from .regras_inferencia import avaliar_regras


class RespostasInsuficientesError(ValueError):
    """Poucas perguntas válidas foram respondidas para gerar uma recomendação."""


@dataclass
class PerfilUsuario:
    nivel: str | None = None
    experiencias: list = field(default_factory=list)
    ferramentas: list = field(default_factory=list)
    objetivos: list = field(default_factory=list)
    preferencias: list = field(default_factory=list)
    respostas: dict = field(default_factory=dict)

    @classmethod
    def de_dict(cls, dados: dict | None) -> "PerfilUsuario":
        """Cria o perfil a partir de um dicionário (como o guardado pela interface)."""
        dados = dados if isinstance(dados, dict) else {}

        def lista(chave):
            valor = dados.get(chave)
            return list(valor) if isinstance(valor, (list, tuple, set)) else []

        respostas = dados.get("respostas")
        return cls(
            nivel=dados.get("nivel"),
            experiencias=lista("experiencias"),
            ferramentas=lista("ferramentas"),
            objetivos=lista("objetivos"),
            preferencias=lista("preferencias"),
            respostas=dict(respostas) if isinstance(respostas, dict) else {},
        )


@dataclass
class ResultadoCarreira:
    id: str
    nome: str
    pontuacao: float                 # 0..100, sem arredondar
    percentual: float                # arredondado conforme parametros.casas_decimais
    posicao: int = 0                 # 1 = melhor; empates dividem a mesma posição
    empatada: bool = False
    componentes: dict = field(default_factory=dict)       # pontos por fator
    detalhe_dimensoes: list = field(default_factory=list)
    ferramentas_relevantes: list = field(default_factory=list)
    objetivos_relevantes: list = field(default_factory=list)
    preferencias_relevantes: list = field(default_factory=list)
    pontos_fortes: list = field(default_factory=list)
    pontos_atencao: list = field(default_factory=list)


@dataclass
class ResultadoAvaliacao:
    ranking: list                    # todas as carreiras, ordenadas
    top: list                        # posições 1 a 3 (inclui empatadas na 3ª posição)
    clareza: str                     # 'clara', 'moderada', 'ambigua' ou 'empate'
    mensagens: list
    avisos: list
    regras_acionadas: list
    alternativas: list
    sem_diferenciacao: bool
    respostas_usadas: dict           # dimensão -> resposta (ou None se imputada)


def normalizar_resposta(valor: int) -> float:
    """Converte a escala 1..5 em 0..1."""
    return (valor - 1) / 4


def converter_resposta(valor):
    """Converte para inteiro 1..5 ou devolve None se for ausente/inválida."""
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, str):
        valor = valor.strip()
        if not valor.lstrip("+-").isdigit():
            return None
        valor = int(valor)
    if isinstance(valor, float):
        if not eh_numero(valor) or not valor.is_integer():
            return None
        valor = int(valor)
    if isinstance(valor, int) and 1 <= valor <= 5:
        return valor
    return None


def validar_respostas(base: dict, respostas) -> tuple:
    """Separa respostas válidas das ausentes/inválidas. Devolve (validas, avisos)."""
    avisos = []
    if not isinstance(respostas, dict):
        if respostas is not None:
            avisos.append("O formato das respostas é inválido; todas foram ignoradas.")
        respostas = {}
    ids = {d["id"]: d["nome"] for d in base["dimensoes"]}
    for chave in respostas:
        if chave not in ids:
            avisos.append(f"Dimensão desconhecida ignorada: '{chave}'.")
    validas = {}
    for dim_id, nome in ids.items():
        bruto = respostas.get(dim_id)
        valor = converter_resposta(bruto)
        if valor is not None:
            validas[dim_id] = valor
        elif bruto is None:
            avisos.append(f"Sem resposta em '{nome}': tratada como neutra.")
        else:
            avisos.append(f"Resposta inválida em '{nome}' ({bruto!r}): tratada como neutra.")
    return validas, avisos


def _ids_validos(lista, conhecidos, rotulo, avisos):
    """Remove duplicatas e ids desconhecidos, mantendo a ordem."""
    saida = []
    for item in lista or []:
        if item in conhecidos:
            if item not in saida:
                saida.append(item)
        else:
            avisos.append(f"{rotulo} desconhecido(a) ignorado(a): {item!r}.")
    return saida


def _regras_posicao(ordenadas, casas):
    """Posição por 'ranking de competição' (1, 2, 2, 4): empates dividem a posição."""
    posicoes, anterior, posicao_atual = [], None, 0
    for indice, item in enumerate(ordenadas):
        chave = round(item.pontuacao, casas)
        if chave != anterior:
            posicao_atual = indice + 1
            anterior = chave
        posicoes.append(posicao_atual)
    return posicoes


def avaliar(base: dict, perfil: PerfilUsuario) -> ResultadoAvaliacao:
    """Calcula compatibilidade com todas as carreiras da base e monta o ranking."""
    par = base["parametros"]
    casas = par["casas_decimais"]
    avisos: list = []

    validas, avisos_resp = validar_respostas(base, perfil.respostas)
    avisos.extend(avisos_resp)
    if len(validas) < par["minimo_dimensoes_respondidas"]:
        raise RespostasInsuficientesError(
            f"Responda pelo menos {par['minimo_dimensoes_respondidas']} das {len(base['dimensoes'])} "
            f"perguntas de afinidade (respostas válidas: {len(validas)}).")

    nomes_dim = {d["id"]: d["nome"] for d in base["dimensoes"]}
    completas = {d: validas.get(d, par["resposta_neutra"]) for d in nomes_dim}
    normalizadas = {d: normalizar_resposta(v) for d, v in completas.items()}

    fatores = {chave: {i["id"]: i for i in base[chave]} for chave in ("ferramentas", "objetivos", "preferencias")}
    ferramentas = _ids_validos(perfil.ferramentas, fatores["ferramentas"], "Ferramenta", avisos)
    objetivos = _ids_validos(perfil.objetivos, fatores["objetivos"], "Objetivo", avisos)
    preferencias = _ids_validos(perfil.preferencias, fatores["preferencias"], "Preferência", avisos)

    niveis = {n["id"]: n for n in base["niveis_conhecimento"]}
    nivel = perfil.nivel if perfil.nivel in niveis else None
    if perfil.nivel is not None and nivel is None:
        avisos.append(f"Nível de conhecimento desconhecido ignorado: {perfil.nivel!r}.")

    resultados = []
    for cid, carreira in base["carreiras"].items():
        w = normalizar_pesos(carreira["pesos"])
        afinidade = sum(w[d] * normalizadas[d] for d in nomes_dim)

        sobra = 1.0
        usadas_ferr = []
        for f in ferramentas:
            r = fatores["ferramentas"][f]["relevancia"].get(cid, 0)
            if r > 0:
                sobra *= (1 - r)
                usadas_ferr.append(fatores["ferramentas"][f]["nome"])
        t = 1 - sobra

        def maximo(chave, ids):
            valores = [(fatores[chave][i]["relevancia"].get(cid, 0), fatores[chave][i]["nome"]) for i in ids]
            valores = [v for v in valores if v[0] > 0]
            return (max(v[0] for v in valores) if valores else 0.0), [v[1] for v in valores]

        o, usados_obj = maximo("objetivos", objetivos)
        p, usadas_pref = maximo("preferencias", preferencias)

        comp = {
            "afinidade": 100 * par["peso_afinidade"] * afinidade,
            "ferramentas": 100 * par["peso_ferramentas"] * t,
            "objetivos": 100 * par["peso_objetivos"] * o,
            "preferencias": 100 * par["peso_preferencias"] * p,
        }
        pontuacao = min(100.0, max(0.0, sum(comp.values())))

        detalhe = []
        for d in nomes_dim:
            detalhe.append({
                "id": d, "nome": nomes_dim[d], "resposta": completas[d],
                "imputada": d not in validas,
                "peso_percentual": 100 * w[d],
                "pontos": 100 * par["peso_afinidade"] * w[d] * normalizadas[d],
                "pontos_maximos": 100 * par["peso_afinidade"] * w[d],
            })

        res = ResultadoCarreira(
            id=cid, nome=carreira["nome"], pontuacao=pontuacao,
            percentual=round(pontuacao, casas), componentes=comp,
            detalhe_dimensoes=detalhe, ferramentas_relevantes=usadas_ferr,
            objetivos_relevantes=usados_obj, preferencias_relevantes=usadas_pref)
        _preencher_justificativas(res, validas)
        resultados.append(res)

    # Ordenação: maior pontuação (no nível de precisão exibido) primeiro; empates mantêm a ordem do JSON.
    ordem_json = {cid: i for i, cid in enumerate(base["carreiras"])}
    resultados.sort(key=lambda r: (-round(r.pontuacao, casas), ordem_json[r.id]))
    for res, pos in zip(resultados, _regras_posicao(resultados, casas)):
        res.posicao = pos
    for res in resultados:
        res.empatada = sum(1 for o in resultados if o.posicao == res.posicao) > 1

    top = [r for r in resultados if r.posicao <= 3]

    # Estatísticas do perfil para as regras de inferência.
    if validas:
        valores = list(validas.values())
        media, amplitude = sum(valores) / len(valores), max(valores) - min(valores)
    else:
        media, amplitude = None, None
    contexto = dict(validas)
    contexto.update({
        "nivel": niveis[nivel]["ordem"] if nivel else None,
        "num_ferramentas": len(ferramentas),
        "media_respostas": media, "amplitude_respostas": amplitude,
    })
    regras = avaliar_regras(base, contexto)

    clareza, mensagens, sem_dif = _classificar(base, resultados, top)
    alternativas = _alternativas(base, resultados, top, regras)

    return ResultadoAvaliacao(
        ranking=resultados, top=top, clareza=clareza, mensagens=mensagens, avisos=avisos,
        regras_acionadas=regras, alternativas=alternativas, sem_diferenciacao=sem_dif,
        respostas_usadas={d: validas.get(d) for d in nomes_dim})


def _preencher_justificativas(res: ResultadoCarreira, validas: dict) -> None:
    """Gera pontos fortes e pontos de atenção a partir das contribuições."""
    relevantes = sorted(res.detalhe_dimensoes, key=lambda d: -d["peso_percentual"])
    for d in relevantes:
        if d["imputada"] or d["peso_percentual"] < 8:
            continue
        texto = (f"{d['nome']}: você respondeu {d['resposta']}/5 e esta dimensão representa "
                 f"{d['peso_percentual']:.0f}% do peso desta trilha.")
        if d["resposta"] >= 4 and len(res.pontos_fortes) < 3:
            res.pontos_fortes.append(texto)
        elif d["resposta"] <= 2 and len(res.pontos_atencao) < 3:
            res.pontos_atencao.append(texto)
    if res.ferramentas_relevantes:
        res.pontos_fortes.append("Ferramentas declaradas relacionadas a esta trilha: "
                                 + ", ".join(res.ferramentas_relevantes) + ".")
    if res.objetivos_relevantes:
        res.pontos_fortes.append("Objetivo profissional alinhado: " + "; ".join(res.objetivos_relevantes) + ".")
    if res.preferencias_relevantes:
        res.pontos_fortes.append("Preferência de atuação alinhada: " + "; ".join(res.preferencias_relevantes) + ".")


def _classificar(base, resultados, top):
    par = base["parametros"]
    casas = par["casas_decimais"]
    mensagens = []
    primeiro = resultados[0]
    empatadas_topo = [r for r in resultados if r.posicao == 1]
    pontuacoes = [r.pontuacao for r in resultados]
    amplitude = max(pontuacoes) - min(pontuacoes)
    sem_dif = len(empatadas_topo) > len(resultados) // 2 or amplitude < 1e-9

    if len(empatadas_topo) > 1:
        nomes = ", ".join(r.nome for r in empatadas_topo)
        clareza = "empate"
        mensagens.append(f"Empate na primeira posição ({primeiro.percentual:.{casas}f}%): {nomes}. "
                         "O modelo não consegue distinguir essas trilhas com as respostas fornecidas.")
    else:
        segundo = resultados[1]
        diferenca = primeiro.pontuacao - segundo.pontuacao
        if round(primeiro.pontuacao, casas) == round(segundo.pontuacao, casas):  # defensivo
            clareza = "empate"
        elif diferenca < par["margem_proximidade"]:
            clareza = "ambigua"
            mensagens.append(f"Resultado ambíguo: {primeiro.nome} e {segundo.nome} diferem em apenas "
                             f"{diferenca:.1f} ponto(s). Trate as duas como candidatas e compare os projetos de portfólio.")
        elif diferenca < par["limite_clareza"]:
            clareza = "moderada"
            mensagens.append(f"A primeira trilha lidera por {diferenca:.1f} pontos: há uma tendência, "
                             "mas as seguintes continuam plausíveis.")
        else:
            clareza = "clara"
            mensagens.append(f"{primeiro.nome} se destaca com {diferenca:.1f} pontos de vantagem sobre a segunda colocada.")

    if len(top) > 3:
        extras = ", ".join(r.nome for r in top[3:])
        mensagens.append(f"Por haver empate na 3ª posição, o resultado inclui mais de três trilhas ({extras}).")
    if sem_dif:
        mensagens.append("Não há diferenciação clara entre as trilhas (perfil equilibrado ou respostas muito semelhantes). "
                         "Use este resultado como ponto de partida e experimente projetos curtos em duas ou três áreas.")
    elif amplitude < par["amplitude_perfil_equilibrado"]:
        mensagens.append(f"As dez trilhas ficaram próximas (amplitude de {amplitude:.1f} pontos): "
                         "seu perfil parece equilibrado ou com interesses variados.")
    return clareza, mensagens, sem_dif


def _alternativas(base, resultados, top, regras):
    """Carreiras fora do top que as regras indicam ou que estão muito próximas da última do top."""
    ids_top = {r.id for r in top}
    por_id = {r.id: r for r in resultados}
    alternativas, vistos = [], set()
    for regra in regras:
        for cid in regra["carreiras"]:
            if cid not in ids_top and cid not in vistos and cid in por_id:
                vistos.add(cid)
                alternativas.append({"id": cid, "nome": por_id[cid].nome,
                                     "motivo": f"Indicada pela regra {regra['id']} ({regra['nome']})."})
    margem = base["parametros"]["margem_proximidade"]
    ultima = min(r.pontuacao for r in top)
    for r in resultados:
        if r.id not in ids_top and r.id not in vistos and ultima - r.pontuacao <= margem:
            vistos.add(r.id)
            alternativas.append({"id": r.id, "nome": r.nome,
                                 "motivo": f"Pontuação a menos de {margem:.0f} ponto(s) da última trilha do ranking."})
    return alternativas[:5]
