"""Interface Streamlit do Consultor Inteligente de Carreiras em TI (Etapa 2).

A interface só cuida de perguntar e exibir. O cálculo fica em carreiras/motor.py,
a análise de lacunas em carreiras/lacunas.py, o roadmap em carreiras/roadmap.py
e todo o conhecimento (pesos, textos, regras) em regras_carreiras.json.
"""
from __future__ import annotations

import copy

import streamlit as st

from carreiras.base_conhecimento import BaseConhecimentoError, carregar_base
from carreiras.lacunas import analisar_lacunas
from carreiras.motor import PerfilUsuario, RespostasInsuficientesError, avaliar
from carreiras.personas import PERSONAS
from carreiras.roadmap import gerar_roadmap

NOMES_ETAPAS = {1: "Perfil pessoal", 2: "Afinidades técnicas", 3: "Resultados"}
OPCOES_ESCALA = [1, 2, 3, 4, 5]
MARCADORES = {"lacuna": "🎯", "aprofundamento": "🔁", "base": "•"}


# ----------------------------------------------------------------- estado
def _dados_vazios() -> dict:
    return {"nivel": None, "experiencias": [], "ferramentas": [],
            "objetivos": [], "preferencias": [], "respostas": {}}


def _iniciar_estado() -> None:
    if "etapa" not in st.session_state:
        st.session_state["etapa"] = 1
    if "dados" not in st.session_state:
        st.session_state["dados"] = _dados_vazios()


def _ir_para(etapa: int) -> None:
    st.session_state["etapa"] = etapa


def _limpar_widgets(manter=()) -> None:
    for chave in list(st.session_state.keys()):
        if chave.startswith(("w_", "q_")) and chave not in manter:
            del st.session_state[chave]


def _reiniciar() -> None:
    for chave in list(st.session_state.keys()):
        del st.session_state[chave]


def _carregar_persona(persona_id: str) -> None:
    _limpar_widgets(manter=("w_persona",))
    dados = _dados_vazios()
    dados.update(copy.deepcopy(PERSONAS[persona_id]["perfil"]))
    st.session_state["dados"] = dados
    st.session_state["etapa"] = 1


def _semear(chave: str, valor) -> None:
    """Restaura um widget a partir dos dados guardados (usado ao voltar de etapa)."""
    if chave not in st.session_state and valor not in (None, [], ""):
        st.session_state[chave] = valor


# ----------------------------------------------------------------- etapas
def etapa_perfil(kb: dict) -> None:
    dados = st.session_state["dados"]
    st.subheader("Etapa 1 — Perfil pessoal")
    st.write("Conte um pouco sobre você. Estas informações ajudam a personalizar o plano de estudos.")

    niveis = {n["id"]: n for n in sorted(kb["niveis_conhecimento"], key=lambda n: n["ordem"])}
    _semear("w_nivel", dados["nivel"])
    dados["nivel"] = st.radio(
        "Qual é o seu nível atual de conhecimento em TI?", list(niveis), index=None,
        format_func=lambda i: f"{niveis[i]['nome']} — {niveis[i]['descricao']}", key="w_nivel")

    for chave_dado, rotulo, lista, ajuda in (
        ("experiencias", "Que experiências prévias você tem?", kb["experiencias"], None),
        ("ferramentas", "Quais linguagens e ferramentas você já conhece?", kb["ferramentas"],
         "Marque apenas o que você já usou. Se ainda não conhece nenhuma, deixe em branco."),
        ("objetivos", "Quais são os seus objetivos profissionais?", kb["objetivos"], None),
        ("preferencias", "Como você prefere atuar?", kb["preferencias"], None),
    ):
        nomes = {i["id"]: i["nome"] for i in lista}
        chave_widget = f"w_{chave_dado}"
        _semear(chave_widget, [v for v in dados[chave_dado] if v in nomes])
        dados[chave_dado] = st.multiselect(rotulo, list(nomes), format_func=lambda i, n=nomes: n[i],
                                           key=chave_widget, help=ajuda)

    if dados["nivel"] is None:
        st.caption("Escolha o seu nível de conhecimento para continuar.")
    st.button("Próxima etapa →", on_click=_ir_para, args=(2,), disabled=dados["nivel"] is None, type="primary")


def etapa_afinidades(kb: dict) -> None:
    dados = st.session_state["dados"]
    escala = kb["escala"]
    minimo = kb["parametros"]["minimo_dimensoes_respondidas"]
    st.subheader("Etapa 2 — Afinidades técnicas")
    st.write("Para cada área, indique o quanto ela combina com você: "
             + ", ".join(f"**{k}** = {v}" for k, v in escala.items()) + ".")

    for numero, dim in enumerate(kb["dimensoes"], start=1):
        chave = f"q_{dim['id']}"
        _semear(chave, dados["respostas"].get(dim["id"]))
        dados["respostas"][dim["id"]] = st.radio(
            f"{numero}. {dim['nome']}", OPCOES_ESCALA, index=None, horizontal=True, key=chave,
            format_func=lambda v: f"{v} · {escala[str(v)]}", help=dim["pergunta"])
        st.caption(dim["pergunta"])

    respondidas = sum(1 for v in dados["respostas"].values() if v is not None)
    total = len(kb["dimensoes"])
    st.progress(respondidas / total, text=f"{respondidas} de {total} perguntas respondidas")
    if respondidas < minimo:
        st.caption(f"Responda pelo menos {minimo} perguntas para ver os resultados.")
    elif respondidas < total:
        st.caption("Perguntas sem resposta serão tratadas como neutras (3) no cálculo.")

    col_voltar, col_avancar = st.columns(2)
    with col_voltar:
        st.button("← Voltar ao perfil", on_click=_ir_para, args=(1,))
    with col_avancar:
        st.button("Ver resultados →", on_click=_ir_para, args=(3,), disabled=respondidas < minimo, type="primary")


def _grafico_comparativo(resultado) -> None:
    dados = [{"Trilha": r.nome, "Compatibilidade (%)": r.percentual} for r in resultado.ranking]
    try:
        import altair as alt
        import pandas as pd
        grafico = alt.Chart(pd.DataFrame(dados)).mark_bar().encode(
            x=alt.X("Compatibilidade (%):Q", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Trilha:N", sort="-x", title=None),
            tooltip=["Trilha", "Compatibilidade (%)"],
        ).properties(height=34 * len(dados))
        st.altair_chart(grafico)
    except ImportError:
        for item in dados:
            st.progress(min(max(item["Compatibilidade (%)"] / 100, 0.0), 1.0),
                        text=f"{item['Trilha']}: {item['Compatibilidade (%)']}%")


def _mostrar_topo(kb: dict, resultado) -> None:
    casas = kb["parametros"]["casas_decimais"]
    if resultado.sem_diferenciacao:
        st.warning("Não há uma trilha que se destaque com as respostas fornecidas. "
                   "Trilhas empatadas: " + ", ".join(r.nome for r in resultado.top) + ".")
        return
    principais = resultado.top[:3]
    colunas = st.columns(len(principais))
    for coluna, r in zip(colunas, principais):
        with coluna:
            marca = " (empate)" if r.empatada else ""
            st.metric(f"{r.posicao}º lugar{marca}", f"{r.percentual:.{casas}f}%")
            st.write(f"**{r.nome}**")
    if len(resultado.top) > 3:
        st.info("Também na 3ª posição por empate: " + ", ".join(r.nome for r in resultado.top[3:]) + ".")


def _mostrar_detalhe(kb: dict, resultado, perfil, carreira_id: str) -> None:
    r = next(x for x in resultado.ranking if x.id == carreira_id)
    carreira = kb["carreiras"][carreira_id]
    analise = analisar_lacunas(kb, carreira_id, perfil)
    roadmap = gerar_roadmap(kb, carreira_id, analise, perfil)
    abas = st.tabs(["Por que esta trilha?", "Lacunas", "Roadmap", "Certificações e projeto"])

    with abas[0]:
        st.write(carreira["descricao"])
        st.write("**Características da trilha:**")
        for item in carreira["caracteristicas"]:
            st.write(f"- {item}")
        if r.pontos_fortes:
            st.write("**Pontos a favor:**")
            for item in r.pontos_fortes:
                st.write(f"- {item}")
        if r.pontos_atencao:
            st.write("**Pontos de atenção:**")
            for item in r.pontos_atencao:
                st.write(f"- {item}")
        with st.expander("Como a pontuação desta trilha foi calculada"):
            st.write("Pontos por fator: " + "; ".join(f"{k} = {v:.1f}" for k, v in r.componentes.items())
                     + f". Total: {r.pontuacao:.1f} de 100.")
            st.table([{"Dimensão": d["nome"], "Sua resposta": d["resposta"] if not d["imputada"] else "neutra (3)",
                       "Peso na trilha (%)": round(d["peso_percentual"], 1),
                       "Pontos": round(d["pontos"], 2), "Máximo": round(d["pontos_maximos"], 2)}
                      for d in r.detalhe_dimensoes])

    with abas[1]:
        st.write(f"Nível informado: **{analise['nivel_usuario']}**. "
                 f"Cobertura declarada das competências de nível Júnior: **{analise['cobertura_declarada_percentual']:.0f}%**.")
        for obs in analise["observacoes"]:
            st.info(obs)
        st.write("**✅ Conhecimentos declarados por você (aprofundar):**")
        if analise["declarados"]:
            for d in analise["declarados"]:
                st.write(f"- **{d['nome']}** — _{d['origem']}_. {d['aprofundamento']}")
        else:
            st.write("- Nenhum conhecimento declarado está ligado a esta trilha.")
        st.write("**🎯 Lacunas presumidas pelo sistema:**")
        if analise["lacunas"]:
            for l in analise["lacunas"]:
                st.write(f"- **{l['nome']}** ({l['prioridade']}) — _{l['origem']}_. {l['descricao']} {l['motivo']}")
        else:
            st.write("- Nenhuma lacuna presumida. Foque em aprofundar o que você já conhece.")

    with abas[2]:
        st.caption("🎯 = vem das suas lacunas · 🔁 = aprofundamento do que você declarou · • = conteúdo padrão da trilha")
        for etapa in roadmap["etapas"]:
            st.markdown(f"**{etapa['titulo']}**")
            if etapa["descricao"]:
                st.write(etapa["descricao"])
            for item in etapa["itens"]:
                st.write(f"{MARCADORES[item['tipo']]} {item['texto']}")

    with abas[3]:
        projeto = roadmap["projeto"]
        st.write(f"**Projeto sugerido para o GitHub:** {projeto['titulo']}")
        st.write(projeto["descricao"])
        for e in projeto["entregaveis"]:
            st.write(f"- {e}")
        st.write("**Certificações opcionais:**")
        for c in roadmap["certificacoes"]:
            obs = f" — {c['observacao']}" if c.get("observacao") else ""
            st.write(f"- {c['nome']} ({c['emissor']}){obs}")
        st.caption(roadmap["aviso_certificacoes"])


def etapa_resultados(kb: dict) -> None:
    dados = st.session_state["dados"]
    st.subheader("Etapa 3 — Resultados")
    perfil = PerfilUsuario.de_dict(dados)
    try:
        resultado = avaliar(kb, perfil)
    except RespostasInsuficientesError as erro:
        st.error(str(erro))
        st.button("← Voltar às afinidades", on_click=_ir_para, args=(2,))
        return

    st.caption("Os percentuais são estimativas de compatibilidade calculadas pelo modelo a partir das suas respostas. "
               "Não são probabilidades de sucesso profissional nem substituem orientação humana.")
    for aviso in resultado.avisos:
        st.warning(aviso)
    for mensagem in resultado.mensagens:
        (st.warning if resultado.clareza in ("ambigua", "empate") else st.info)(mensagem)

    _mostrar_topo(kb, resultado)

    st.write("**Comparativo das trilhas**")
    _grafico_comparativo(resultado)

    if resultado.alternativas:
        with st.expander("Alternativas compatíveis"):
            for alt in resultado.alternativas:
                st.write(f"- **{alt['nome']}**: {alt['motivo']}")
    if resultado.regras_acionadas:
        with st.expander("Regras de inferência acionadas"):
            for regra in resultado.regras_acionadas:
                st.write(f"- **{regra['id']} · {regra['nome']}**: {regra['mensagem']}")

    st.divider()
    ids = [r.id for r in resultado.ranking]
    posicoes = {r.id: r for r in resultado.ranking}
    escolhido = st.selectbox(
        "Ver plano detalhado de:", ids, key="w_detalhe",
        format_func=lambda i: f"{posicoes[i].posicao}º · {posicoes[i].nome} ({posicoes[i].percentual}%)")
    _mostrar_detalhe(kb, resultado, perfil, escolhido)

    st.divider()
    st.button("← Voltar e editar respostas", on_click=_ir_para, args=(2,))


# ----------------------------------------------------------------- principal
def main() -> None:
    st.set_page_config(page_title="Consultor de Carreiras em TI", page_icon="💻", layout="centered")
    try:
        kb = carregar_base()
    except BaseConhecimentoError as erro:
        st.error("Não foi possível carregar a base de conhecimento (regras_carreiras.json).")
        for item in erro.erros[:20]:
            st.write(f"- {item}")
        st.stop()
        return

    _iniciar_estado()

    with st.sidebar:
        st.subheader("Perfis de demonstração")
        persona_id = st.selectbox("Escolha um perfil", list(PERSONAS), key="w_persona",
                                  format_func=lambda i: PERSONAS[i]["nome"])
        st.caption(PERSONAS[persona_id]["descricao"])
        st.button("Carregar perfil", on_click=_carregar_persona, args=(persona_id,))
        st.divider()
        st.button("🔄 Reiniciar avaliação", on_click=_reiniciar)

    st.title("Consultor Inteligente de Carreiras em TI")
    st.caption("Orientação inicial baseada em um modelo de pontuação ponderada. "
               "Não substitui pesquisa, experiência prática ou aconselhamento profissional.")
    etapa = st.session_state["etapa"]
    st.progress(etapa / 3, text=f"Etapa {etapa} de 3 — {NOMES_ETAPAS[etapa]}")

    if etapa == 1:
        etapa_perfil(kb)
    elif etapa == 2:
        etapa_afinidades(kb)
    else:
        etapa_resultados(kb)


if __name__ == "__main__":
    main()
