import copy
import json
import tempfile
import unittest
from pathlib import Path

from carreiras.base_conhecimento import (
    CARREIRAS_OBRIGATORIAS, ETAPAS_ROADMAP, BaseConhecimentoError,
    carregar_base, normalizar_pesos, validar_base)
from tests.utilitarios import base_copia


class TestCarregamento(unittest.TestCase):
    def test_base_json_carrega(self):
        base = carregar_base()
        self.assertIsInstance(base, dict)

    def test_dez_carreiras_obrigatorias_presentes(self):
        base = carregar_base()
        for cid in CARREIRAS_OBRIGATORIAS:
            self.assertIn(cid, base["carreiras"])
        self.assertEqual(len(CARREIRAS_OBRIGATORIAS), 10)

    def test_pesos_validos_e_normalizaveis(self):
        base = carregar_base()
        cap = base["parametros"]["peso_maximo_por_dimensao"]
        ids_dim = {d["id"] for d in base["dimensoes"]}
        for cid, carreira in base["carreiras"].items():
            self.assertEqual(set(carreira["pesos"]), ids_dim, cid)
            normalizados = normalizar_pesos(carreira["pesos"])
            self.assertAlmostEqual(sum(normalizados.values()), 1.0, places=9, msg=cid)
            self.assertLessEqual(max(normalizados.values()), cap + 1e-9, cid)
            self.assertTrue(all(0 <= v <= 10 for v in carreira["pesos"].values()), cid)

    def test_pesos_dos_fatores_somam_um(self):
        p = carregar_base()["parametros"]
        soma = p["peso_afinidade"] + p["peso_ferramentas"] + p["peso_objetivos"] + p["peso_preferencias"]
        self.assertAlmostEqual(soma, 1.0, places=6)

    def test_cada_carreira_tem_conteudo_completo(self):
        base = carregar_base()
        for cid, c in base["carreiras"].items():
            self.assertTrue(c["competencias_junior"], cid)
            self.assertTrue(c["certificacoes_opcionais"], cid)
            self.assertTrue(c["projeto_portfolio"]["entregaveis"], cid)
            for etapa in ETAPAS_ROADMAP:
                self.assertTrue(c["roadmap"][etapa], f"{cid}:{etapa}")

    def test_arquivo_ausente(self):
        with self.assertRaises(BaseConhecimentoError) as ctx:
            carregar_base(Path(tempfile.gettempdir()) / "nao_existe_regras.json")
        self.assertIn("não encontrado", ctx.exception.erros[0])

    def test_json_invalido(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "ruim.json"
            caminho.write_text("{ isto não é json", encoding="utf-8")
            with self.assertRaises(BaseConhecimentoError) as ctx:
                carregar_base(caminho)
            self.assertIn("JSON inválido", ctx.exception.erros[0])

    def test_json_valido_copiado_para_outro_caminho(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "copia.json"
            caminho.write_text(json.dumps(base_copia(), ensure_ascii=False), encoding="utf-8")
            self.assertEqual(len(carregar_base(caminho)["carreiras"]), 10)


class TestValidacao(unittest.TestCase):
    def test_base_original_sem_erros(self):
        self.assertEqual(validar_base(carregar_base()), [])

    def test_raiz_nao_objeto(self):
        self.assertTrue(validar_base([1, 2]))

    def test_chave_raiz_ausente(self):
        base = base_copia()
        del base["regras_inferencia"]
        self.assertTrue(any("regras_inferencia" in e for e in validar_base(base)))

    def test_carreira_obrigatoria_ausente(self):
        base = base_copia()
        del base["carreiras"]["qa"]
        self.assertTrue(any("qa" in e for e in validar_base(base)))

    def test_campo_obrigatorio_vazio(self):
        base = base_copia()
        base["carreiras"]["backend"]["descricao"] = "  "
        self.assertTrue(any("descricao" in e for e in validar_base(base)))

    def test_peso_negativo(self):
        base = base_copia()
        base["carreiras"]["backend"]["pesos"]["logica"] = -1
        self.assertTrue(any("logica" in e for e in validar_base(base)))

    def test_peso_acima_do_maximo(self):
        base = base_copia()
        base["carreiras"]["backend"]["pesos"]["logica"] = 11
        self.assertTrue(validar_base(base))

    def test_peso_nao_numerico_ou_booleano(self):
        for invalido in ("alto", True, None):
            base = base_copia()
            base["carreiras"]["backend"]["pesos"]["logica"] = invalido
            self.assertTrue(validar_base(base), invalido)

    def test_dimensao_faltando_nos_pesos(self):
        base = base_copia()
        del base["carreiras"]["devops"]["pesos"]["infra"]
        self.assertTrue(any("infra" in e for e in validar_base(base)))

    def test_dimensao_desconhecida_nos_pesos(self):
        base = base_copia()
        base["carreiras"]["devops"]["pesos"]["astrologia"] = 3
        self.assertTrue(any("astrologia" in e for e in validar_base(base)))

    def test_soma_de_pesos_zero(self):
        base = base_copia()
        base["carreiras"]["backend"]["pesos"] = {k: 0 for k in base["carreiras"]["backend"]["pesos"]}
        self.assertTrue(any("maior que zero" in e for e in validar_base(base)))

    def test_dimensao_dominante_e_rejeitada(self):
        base = base_copia()
        pesos = {k: 0 for k in base["carreiras"]["backend"]["pesos"]}
        pesos["logica"] = 10
        base["carreiras"]["backend"]["pesos"] = pesos
        self.assertTrue(any("acima do limite" in e for e in validar_base(base)))

    def test_pesos_dos_fatores_que_nao_somam_um(self):
        base = base_copia()
        base["parametros"]["peso_afinidade"] = 0.5
        self.assertTrue(any("somar 1" in e for e in validar_base(base)))

    def test_ferramenta_desconhecida_em_competencia(self):
        base = base_copia()
        base["carreiras"]["backend"]["competencias_junior"][0]["ferramentas_relacionadas"] = ["inexistente"]
        self.assertTrue(any("inexistente" in e for e in validar_base(base)))

    def test_roadmap_incompleto(self):
        base = base_copia()
        base["carreiras"]["cloud"]["roadmap"]["fundamentos"] = []
        self.assertTrue(any("fundamentos" in e for e in validar_base(base)))

    def test_relevancia_fora_do_intervalo(self):
        base = base_copia()
        base["ferramentas"][0]["relevancia"]["backend"] = 1.5
        self.assertTrue(validar_base(base))

    def test_regra_com_campo_inexistente(self):
        base = base_copia()
        base["regras_inferencia"][0]["condicoes"][0]["campo"] = "campo_falso"
        self.assertTrue(any("condição inválida" in e for e in validar_base(base)))

    def test_erro_de_validacao_lista_todos_os_problemas(self):
        base = base_copia()
        base["carreiras"]["backend"]["descricao"] = ""
        base["carreiras"]["qa"]["pesos"]["testes"] = -5
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "dois_erros.json"
            caminho.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(BaseConhecimentoError) as ctx:
                carregar_base(caminho)
        self.assertGreaterEqual(len(ctx.exception.erros), 2)


class TestNormalizarPesos(unittest.TestCase):
    def test_soma_um(self):
        self.assertAlmostEqual(sum(normalizar_pesos({"a": 2, "b": 6}).values()), 1.0)

    def test_soma_zero_levanta_erro(self):
        with self.assertRaises(ValueError):
            normalizar_pesos({"a": 0, "b": 0})


if __name__ == "__main__":
    unittest.main()
