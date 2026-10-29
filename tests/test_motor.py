import copy
import unittest

from carreiras.base_conhecimento import carregar_base, validar_base
from carreiras.motor import (
    PerfilUsuario, RespostasInsuficientesError, avaliar, converter_resposta,
    normalizar_resposta, validar_respostas)
from tests.utilitarios import base_copia, respostas_iguais


class TestNormalizacao(unittest.TestCase):
    def test_extremos_e_meio(self):
        self.assertEqual(normalizar_resposta(1), 0.0)
        self.assertEqual(normalizar_resposta(3), 0.5)
        self.assertEqual(normalizar_resposta(5), 1.0)

    def test_conversao_de_respostas(self):
        for bom, esperado in ((1, 1), (5, 5), ("4", 4), (3.0, 3), (" 2 ", 2)):
            self.assertEqual(converter_resposta(bom), esperado)
        for ruim in (None, 0, 6, -1, 2.5, "abc", "", True, False, [], {}, float("nan"), float("inf")):
            self.assertIsNone(converter_resposta(ruim), repr(ruim))


class TestPontuacao(unittest.TestCase):
    def setUp(self):
        self.base = carregar_base()

    def _avaliar(self, respostas, **extra):
        return avaliar(self.base, PerfilUsuario(respostas=respostas, **extra))

    def test_pontuacao_sempre_entre_0_e_100(self):
        casos = [respostas_iguais(v) for v in range(1, 6)]
        todas_ferr = [f["id"] for f in self.base["ferramentas"]]
        todos_obj = [o["id"] for o in self.base["objetivos"]]
        todas_pref = [p["id"] for p in self.base["preferencias"]]
        for respostas in casos:
            for extra in ({}, {"ferramentas": todas_ferr, "objetivos": todos_obj, "preferencias": todas_pref}):
                resultado = self._avaliar(respostas, **extra)
                for r in resultado.ranking:
                    self.assertGreaterEqual(r.pontuacao, 0)
                    self.assertLessEqual(r.pontuacao, 100)
                    self.assertGreaterEqual(r.percentual, 0)
                    self.assertLessEqual(r.percentual, 100)

    def test_todas_respostas_minimas_e_maximas(self):
        minimo = self._avaliar(respostas_iguais(1))
        self.assertTrue(all(r.pontuacao == 0 for r in minimo.ranking))
        maximo = self._avaliar(respostas_iguais(5))
        self.assertTrue(all(abs(r.pontuacao - 80.0) < 1e-9 for r in maximo.ranking))

    def test_ranking_ordenado_e_com_dez_carreiras(self):
        resultado = self._avaliar({"logica": 5, "matematica": 4, "design": 1, "dados": 5, "infra": 2,
                                   "seguranca": 2, "automacao": 3, "testes": 2, "mobile": 1, "negocios": 3})
        pontos = [r.pontuacao for r in resultado.ranking]
        self.assertEqual(len(resultado.ranking), 10)
        self.assertEqual(pontos, sorted(pontos, reverse=True))
        self.assertEqual(resultado.ranking[0].posicao, 1)
        self.assertEqual(resultado.top[0].id, resultado.ranking[0].id)

    def test_formula_confere_com_calculo_manual(self):
        respostas = {"logica": 5, "matematica": 1, "design": 3, "dados": 4, "infra": 2,
                     "seguranca": 5, "automacao": 1, "testes": 3, "mobile": 2, "negocios": 4}
        resultado = self._avaliar(respostas)
        p = self.base["parametros"]
        for r in resultado.ranking:
            pesos = self.base["carreiras"][r.id]["pesos"]
            total = sum(pesos.values())
            manual = sum(pesos[d] / total * (respostas[d] - 1) / 4 for d in pesos)
            self.assertAlmostEqual(r.pontuacao, 100 * p["peso_afinidade"] * manual, places=9)

    def test_fatores_complementares_limitados(self):
        base_sem = self._avaliar(respostas_iguais(3))
        tudo = self._avaliar(respostas_iguais(3),
                             ferramentas=[f["id"] for f in self.base["ferramentas"]],
                             objetivos=[o["id"] for o in self.base["objetivos"]],
                             preferencias=[p["id"] for p in self.base["preferencias"]])
        p = self.base["parametros"]
        limite = 100 * (p["peso_ferramentas"] + p["peso_objetivos"] + p["peso_preferencias"])
        antes = {r.id: r.pontuacao for r in base_sem.ranking}
        for r in tudo.ranking:
            self.assertLessEqual(r.pontuacao - antes[r.id], limite + 1e-9)

    def test_uma_resposta_nao_decide_sozinha(self):
        base_resp = respostas_iguais(3)
        antes = {r.id: r.pontuacao for r in self._avaliar(base_resp).ranking}
        cap = self.base["parametros"]["peso_maximo_por_dimensao"]
        limite = 100 * self.base["parametros"]["peso_afinidade"] * cap
        for dim in base_resp:
            for novo in (1, 5):
                alterada = dict(base_resp, **{dim: novo})
                for r in self._avaliar(alterada).ranking:
                    # variação de uma dimensão 3 -> 1/5 mexe em metade da escala
                    self.assertLessEqual(abs(r.pontuacao - antes[r.id]), limite / 2 + 1e-9)

    def test_componentes_somam_a_pontuacao(self):
        r = self._avaliar(respostas_iguais(4), ferramentas=["python"], objetivos=["proteger"])
        for item in r.ranking:
            self.assertAlmostEqual(sum(item.componentes.values()), item.pontuacao, places=9)

    def test_resultado_deterministico(self):
        a = self._avaliar(respostas_iguais(4), ferramentas=["python", "sql"])
        b = self._avaliar(respostas_iguais(4), ferramentas=["python", "sql"])
        self.assertEqual([(r.id, r.pontuacao) for r in a.ranking], [(r.id, r.pontuacao) for r in b.ranking])

    def test_ferramentas_duplicadas_nao_inflam_pontuacao(self):
        uma = self._avaliar(respostas_iguais(3), ferramentas=["python"])
        varias = self._avaliar(respostas_iguais(3), ferramentas=["python", "python", "python"])
        self.assertEqual([r.pontuacao for r in uma.ranking], [r.pontuacao for r in varias.ranking])

    def test_ferramenta_conhecida_aumenta_a_carreira_relacionada(self):
        sem = {r.id: r.pontuacao for r in self._avaliar(respostas_iguais(3)).ranking}
        com = {r.id: r.pontuacao for r in self._avaliar(respostas_iguais(3), ferramentas=["mobile_framework"]).ranking}
        self.assertGreater(com["mobile"], sem["mobile"])
        self.assertEqual(com["cloud"], sem["cloud"])


class TestEmpates(unittest.TestCase):
    def test_todas_respostas_iguais_gera_empate_total(self):
        base = carregar_base()
        resultado = avaliar(base, PerfilUsuario(respostas=respostas_iguais(3)))
        self.assertEqual(resultado.clareza, "empate")
        self.assertTrue(resultado.sem_diferenciacao)
        self.assertTrue(all(r.posicao == 1 and r.empatada for r in resultado.ranking))
        self.assertEqual(len(resultado.top), 10)
        self.assertTrue(any("Empate" in m for m in resultado.mensagens))

    def test_empate_na_terceira_posicao_preserva_todas(self):
        base = base_copia()
        # cria duas carreiras idênticas à de QA para forçar empate real
        for novo in ("qa_copia_1", "qa_copia_2"):
            clone = copy.deepcopy(base["carreiras"]["qa"])
            clone["nome"] = novo
            base["carreiras"][novo] = clone
        self.assertEqual(validar_base(base), [])
        respostas = {"logica": 2, "matematica": 1, "design": 1, "dados": 1, "infra": 1,
                     "seguranca": 1, "automacao": 4, "testes": 5, "mobile": 1, "negocios": 3}
        resultado = avaliar(base, PerfilUsuario(respostas=respostas))
        empatadas = [r for r in resultado.ranking if r.id.startswith("qa")]
        self.assertEqual(len({r.pontuacao for r in empatadas}), 1)
        self.assertEqual(len({r.posicao for r in empatadas}), 1)
        self.assertTrue(all(r.empatada for r in empatadas))
        ids_top = {r.id for r in resultado.top}
        self.assertTrue({"qa", "qa_copia_1", "qa_copia_2"} <= ids_top)

    def test_posicoes_seguem_ranking_de_competicao(self):
        base = base_copia()
        clone = copy.deepcopy(base["carreiras"]["qa"])
        clone["nome"] = "QA gêmea"
        base["carreiras"]["qa_gemea"] = clone
        resultado = avaliar(base, PerfilUsuario(respostas=respostas_iguais(4) | {"testes": 5}))
        posicoes = [r.posicao for r in resultado.ranking]
        self.assertEqual(posicoes, sorted(posicoes))
        gemeas = [r for r in resultado.ranking if r.id in ("qa", "qa_gemea")]
        self.assertEqual(gemeas[0].posicao, gemeas[1].posicao)
        proxima = [r.posicao for r in resultado.ranking if r.posicao > gemeas[0].posicao]
        self.assertEqual(min(proxima), gemeas[0].posicao + 2)

    def test_resultado_ambiguo_e_sinalizado(self):
        base = carregar_base()
        # busca um perfil com 1º e 2º muito próximos usando ferramentas para ajustar
        resultado = avaliar(base, PerfilUsuario(respostas={
            "logica": 5, "matematica": 4, "design": 2, "dados": 5, "infra": 3,
            "seguranca": 2, "automacao": 4, "testes": 3, "mobile": 1, "negocios": 2},
            ferramentas=["python", "sql"]))
        self.assertEqual(resultado.clareza, "ambigua")
        self.assertTrue(any("ambíguo" in m for m in resultado.mensagens))


class TestRespostasInvalidas(unittest.TestCase):
    def setUp(self):
        self.base = carregar_base()

    def test_respostas_ausentes_viram_neutras_com_aviso(self):
        respostas = respostas_iguais(5)
        del respostas["mobile"]
        respostas["negocios"] = None
        resultado = avaliar(self.base, PerfilUsuario(respostas=respostas))
        self.assertEqual(resultado.respostas_usadas["mobile"], None)
        self.assertGreaterEqual(sum("Sem resposta" in a for a in resultado.avisos), 2)
        detalhe = next(r for r in resultado.ranking if r.id == "mobile").detalhe_dimensoes
        self.assertTrue(next(d for d in detalhe if d["id"] == "mobile")["imputada"])

    def test_respostas_invalidas_sao_ignoradas_com_aviso(self):
        respostas = respostas_iguais(4)
        respostas.update({"logica": 9, "dados": "muito", "infra": True, "design": -2})
        resultado = avaliar(self.base, PerfilUsuario(respostas=respostas))
        self.assertGreaterEqual(sum("inválida" in a for a in resultado.avisos), 4)
        for r in resultado.ranking:
            self.assertTrue(0 <= r.pontuacao <= 100)

    def test_respostas_insuficientes_levantam_erro(self):
        with self.assertRaises(RespostasInsuficientesError):
            avaliar(self.base, PerfilUsuario(respostas={"logica": 5, "dados": 5}))
        with self.assertRaises(RespostasInsuficientesError):
            avaliar(self.base, PerfilUsuario())

    def test_exatamente_o_minimo_de_respostas_funciona(self):
        minimo = self.base["parametros"]["minimo_dimensoes_respondidas"]
        ids = [d["id"] for d in self.base["dimensoes"]][:minimo]
        resultado = avaliar(self.base, PerfilUsuario(respostas={i: 4 for i in ids}))
        self.assertEqual(len(resultado.ranking), 10)

    def test_formato_de_respostas_invalido(self):
        for lixo in ("texto", 42, [1, 2, 3]):
            with self.assertRaises(RespostasInsuficientesError):
                avaliar(self.base, PerfilUsuario(respostas=lixo))

    def test_ids_desconhecidos_geram_aviso_sem_quebrar(self):
        resultado = avaliar(self.base, PerfilUsuario(
            respostas=dict(respostas_iguais(3), astrologia=5), nivel="mestre",
            ferramentas=["cobol_quantico", "python"], objetivos=["x"], preferencias=["y"]))
        texto = " ".join(resultado.avisos)
        for trecho in ("astrologia", "mestre", "cobol_quantico", "'x'", "'y'"):
            self.assertIn(trecho, texto)

    def test_de_dict_tolera_dados_malformados(self):
        for lixo in (None, {}, "x", {"ferramentas": "python", "respostas": "?"}):
            perfil = PerfilUsuario.de_dict(lixo)
            self.assertEqual(perfil.respostas, {})
            self.assertEqual(perfil.ferramentas, [])

    def test_validar_respostas_devolve_apenas_validas(self):
        validas, avisos = validar_respostas(self.base, {"logica": "5", "dados": 0})
        self.assertEqual(validas, {"logica": 5})
        self.assertTrue(avisos)


class TestRegrasDeInferencia(unittest.TestCase):
    def test_regra_dados_programacao_dispara(self):
        base = carregar_base()
        resultado = avaliar(base, PerfilUsuario(respostas=respostas_iguais(3) | {"dados": 5, "logica": 5}))
        self.assertIn("R01", [r["id"] for r in resultado.regras_acionadas])

    def test_regra_iniciante_sem_ferramentas(self):
        base = carregar_base()
        resultado = avaliar(base, PerfilUsuario(nivel="iniciante", respostas=respostas_iguais(3)))
        self.assertIn("R10", [r["id"] for r in resultado.regras_acionadas])
        resultado = avaliar(base, PerfilUsuario(nivel="iniciante", ferramentas=["python"], respostas=respostas_iguais(3)))
        self.assertNotIn("R10", [r["id"] for r in resultado.regras_acionadas])

    def test_alternativas_nao_repetem_o_top(self):
        base = carregar_base()
        resultado = avaliar(base, PerfilUsuario(respostas=respostas_iguais(3) | {"dados": 5, "logica": 5}))
        ids_top = {r.id for r in resultado.top}
        for alt in resultado.alternativas:
            self.assertNotIn(alt["id"], ids_top)


class TestNovaCarreira(unittest.TestCase):
    def test_adicionar_carreira_sem_mudar_codigo(self):
        base = base_copia()
        nova = copy.deepcopy(base["carreiras"]["backend"])
        nova["nome"] = "Engenharia de Jogos"
        nova["pesos"] = dict(nova["pesos"], design=8, matematica=7)
        base["carreiras"]["jogos"] = nova
        self.assertEqual(validar_base(base), [])
        resultado = avaliar(base, PerfilUsuario(respostas=respostas_iguais(3)))
        self.assertEqual(len(resultado.ranking), 11)


if __name__ == "__main__":
    unittest.main()
