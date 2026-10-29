import unittest

from carreiras.base_conhecimento import carregar_base
from carreiras.motor import PerfilUsuario, avaliar
from carreiras.personas import PERSONAS


class TestPersonas(unittest.TestCase):
    def setUp(self):
        self.base = carregar_base()

    def _avaliar(self, persona_id):
        return avaliar(self.base, PerfilUsuario.de_dict(PERSONAS[persona_id]["perfil"]))

    def test_personas_minimas_existem(self):
        for pid in ("analitica", "visual", "infra_seguranca", "negocios_produto",
                    "ambigua_dados_programacao", "iniciante"):
            self.assertIn(pid, PERSONAS)

    def test_expectativas_de_todas_as_personas(self):
        for pid, persona in PERSONAS.items():
            resultado = self._avaliar(pid)
            ids_top = [r.id for r in resultado.top]
            if persona["esperado_primeiro"]:
                self.assertEqual(resultado.ranking[0].id, persona["esperado_primeiro"], pid)
            for cid in persona["esperado_top3"]:
                self.assertIn(cid, ids_top, f"{pid}: {cid} deveria estar no top 3 ({ids_top})")

    def test_persona_analitica(self):
        r = self._avaliar("analitica")
        self.assertEqual(r.top[0].id, "data_science")
        self.assertEqual(r.clareza, "clara")

    def test_persona_visual(self):
        self.assertEqual(self._avaliar("visual").top[0].id, "frontend")

    def test_persona_infra_seguranca(self):
        r = self._avaliar("infra_seguranca")
        self.assertEqual(r.top[0].id, "security")
        self.assertTrue({"cloud", "devops"} <= {x.id for x in r.top})

    def test_persona_negocios(self):
        self.assertEqual(self._avaliar("negocios_produto").top[0].id, "product")

    def test_persona_ambigua_nao_forca_falsa_precisao(self):
        r = self._avaliar("ambigua_dados_programacao")
        self.assertEqual(r.clareza, "ambigua")
        self.assertTrue({"data_science", "data_engineering", "backend"} <= {x.id for x in r.top})
        self.assertTrue(r.mensagens)
        self.assertTrue({"R01"} <= {x["id"] for x in r.regras_acionadas})

    def test_persona_iniciante_recebe_avisos_e_regra_especifica(self):
        r = self._avaliar("iniciante")
        ids_regras = {x["id"] for x in r.regras_acionadas}
        self.assertIn("R10", ids_regras)
        self.assertIn(r.clareza, ("ambigua", "moderada"))

    def test_persona_design_mobile(self):
        r = self._avaliar("design_mobile")
        self.assertEqual({x.id for x in r.top[:2]}, {"mobile", "frontend"})
        self.assertIn("R02", {x["id"] for x in r.regras_acionadas})

    def test_persona_equilibrada_gera_empate(self):
        r = self._avaliar("equilibrada")
        self.assertEqual(r.clareza, "empate")
        self.assertTrue(r.sem_diferenciacao)

    def test_perfil_so_com_respostas_moderadas_nao_destaca_ninguem(self):
        respostas = {d["id"]: 3 for d in self.base["dimensoes"]}
        respostas["logica"] = 4
        respostas["negocios"] = 2
        r = avaliar(self.base, PerfilUsuario(respostas=respostas))
        amplitude = max(x.pontuacao for x in r.ranking) - min(x.pontuacao for x in r.ranking)
        self.assertLess(amplitude, self.base["parametros"]["amplitude_perfil_equilibrado"])
        self.assertIn("R13", {x["id"] for x in r.regras_acionadas})

    def test_perfis_de_personas_sao_independentes_do_original(self):
        PerfilUsuario.de_dict(PERSONAS["analitica"]["perfil"]).ferramentas.append("x")
        self.assertNotIn("x", PERSONAS["analitica"]["perfil"]["ferramentas"])


if __name__ == "__main__":
    unittest.main()
