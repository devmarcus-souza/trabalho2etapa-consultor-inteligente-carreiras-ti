"""Teste de fumaça da interface (app.py) com um Streamlit SIMULADO.

Não abre navegador nem exige o Streamlit instalado: um módulo falso registra as
chamadas, devolve o valor guardado em session_state e permite acionar os
callbacks dos botões. Serve para detectar erros de nome, chave ou fluxo entre as
três etapas. Não substitui testar a interface de verdade com `streamlit run app.py`.
"""
import importlib
import sys
import types
import unittest
from unittest import mock

from carreiras.personas import PERSONAS


class _Contexto:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FalsoStreamlit(types.ModuleType):
    def __init__(self):
        super().__init__("streamlit")
        self.session_state = {}
        self.chamadas = []
        self.botoes = {}

    def _reg(self, nome, *args, **kwargs):
        self.chamadas.append((nome, args, kwargs))

    def __getattr__(self, nome):
        if nome.startswith("__"):
            raise AttributeError(nome)

        def generica(*args, **kwargs):
            self._reg(nome, *args, **kwargs)
        return generica

    def _valor(self, opcoes, kwargs, vazio):
        chave = kwargs.get("key")
        if chave in self.session_state:
            return self.session_state[chave]
        indice = kwargs.get("index", 0)
        return opcoes[indice] if indice is not None and opcoes else vazio

    def radio(self, rotulo, opcoes, **kwargs):
        self._reg("radio", rotulo, **kwargs)
        return self._valor(list(opcoes), kwargs, None)

    def selectbox(self, rotulo, opcoes, **kwargs):
        self._reg("selectbox", rotulo, **kwargs)
        return self._valor(list(opcoes), kwargs, None)

    def multiselect(self, rotulo, opcoes, **kwargs):
        self._reg("multiselect", rotulo, **kwargs)
        return list(self.session_state.get(kwargs.get("key"), []))

    def button(self, rotulo, **kwargs):
        self._reg("button", rotulo, **kwargs)
        self.botoes[rotulo] = kwargs
        return False

    def columns(self, n, **kwargs):
        n = n if isinstance(n, int) else len(n)
        return [_Contexto() for _ in range(n)]

    def tabs(self, rotulos):
        return [_Contexto() for _ in rotulos]

    def expander(self, *a, **k):
        return _Contexto()

    @property
    def sidebar(self):
        return _Contexto()

    def __enter__(self):
        return self

    def textos(self):
        return " ".join(str(a) for _, args, _ in self.chamadas for a in args if isinstance(a, str))

    def clicar(self, rotulo):
        """Executa o callback associado ao botão (como o Streamlit faria antes de rodar de novo)."""
        botao = self.botoes[rotulo]
        self.assert_habilitado(rotulo)
        botao["on_click"](*botao.get("args", ()))

    def assert_habilitado(self, rotulo):
        if self.botoes[rotulo].get("disabled"):
            raise AssertionError(f"Botão desabilitado: {rotulo}")


class TestInterfaceFumaca(unittest.TestCase):
    def setUp(self):
        self.st = FalsoStreamlit()
        self.patch = mock.patch.dict(sys.modules, {"streamlit": self.st})
        self.patch.start()
        sys.modules.pop("app", None)
        self.app = importlib.import_module("app")

    def tearDown(self):
        sys.modules.pop("app", None)
        self.patch.stop()

    def executar(self):
        self.st.chamadas.clear()
        self.st.botoes.clear()
        self.app.main()

    def test_fluxo_completo_com_persona(self):
        self.executar()                                   # etapa 1 vazia
        self.assertIn("Etapa 1", self.st.textos())
        self.assertTrue(self.st.botoes["Próxima etapa →"]["disabled"])

        self.st.clicar("Carregar perfil")                 # carrega a primeira persona do menu
        self.assertEqual(self.st.session_state["etapa"], 1)
        # simula os widgets restaurando o valor guardado
        dados = self.st.session_state["dados"]
        self.st.session_state["w_nivel"] = dados["nivel"]
        self.executar()
        self.assertFalse(self.st.botoes["Próxima etapa →"].get("disabled"))

        self.st.clicar("Próxima etapa →")
        for dim, valor in dados["respostas"].items():
            self.st.session_state[f"q_{dim}"] = valor
        self.executar()                                   # etapa 2
        self.assertIn("Etapa 2", self.st.textos())
        self.assertFalse(self.st.botoes["Ver resultados →"].get("disabled"))

        self.st.clicar("Ver resultados →")
        self.executar()                                   # etapa 3
        texto = self.st.textos()
        self.assertIn("Resultados", texto)
        self.assertIn("estimativas de compatibilidade", texto)
        self.assertIn("Lacunas", texto)

    def test_resultados_sem_respostas_suficientes_mostram_erro(self):
        self.st.session_state["etapa"] = 3
        self.st.session_state["dados"] = {"nivel": "basico", "experiencias": [], "ferramentas": [],
                                          "objetivos": [], "preferencias": [], "respostas": {"logica": 4}}
        self.executar()
        nomes = [c[0] for c in self.st.chamadas]
        self.assertIn("error", nomes)

    def test_voltar_preserva_respostas(self):
        persona = PERSONAS["visual"]["perfil"]
        self.st.session_state["etapa"] = 2
        self.st.session_state["dados"] = {**persona, "respostas": dict(persona["respostas"])}
        self.executar()
        self.st.clicar("← Voltar ao perfil")
        self.assertEqual(self.st.session_state["etapa"], 1)
        self.assertEqual(self.st.session_state["dados"]["respostas"], persona["respostas"])

    def test_reiniciar_limpa_tudo(self):
        self.executar()
        self.st.session_state["dados"]["nivel"] = "basico"
        self.st.clicar("🔄 Reiniciar avaliação")
        self.assertEqual(self.st.session_state, {})

    def test_todas_as_personas_chegam_aos_resultados(self):
        for pid, persona in PERSONAS.items():
            with self.subTest(persona=pid):
                self.st.session_state.clear()
                self.st.session_state["etapa"] = 3
                self.st.session_state["dados"] = {**persona["perfil"], "respostas": dict(persona["perfil"]["respostas"])}
                self.executar()
                self.assertNotIn("error", [c[0] for c in self.st.chamadas])

    def test_base_invalida_mostra_erro_e_nao_quebra(self):
        from carreiras.base_conhecimento import BaseConhecimentoError
        with mock.patch.object(self.app, "carregar_base", side_effect=BaseConhecimentoError(["falhou"])):
            self.executar()
        self.assertIn("error", [c[0] for c in self.st.chamadas])
        self.assertIn("falhou", self.st.textos())


if __name__ == "__main__":
    unittest.main()
