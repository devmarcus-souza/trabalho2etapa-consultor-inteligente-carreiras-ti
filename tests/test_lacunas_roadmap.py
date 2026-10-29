import unittest

from carreiras.base_conhecimento import CARREIRAS_OBRIGATORIAS, ETAPAS_ROADMAP, carregar_base
from carreiras.lacunas import ORIGEM_DECLARADO, ORIGEM_PRESUMIDA, analisar_lacunas
from carreiras.motor import PerfilUsuario
from carreiras.roadmap import TITULOS_ETAPAS, gerar_roadmap


class TestLacunas(unittest.TestCase):
    def setUp(self):
        self.base = carregar_base()

    def test_dados_coerentes_para_todas_as_carreiras(self):
        perfil = PerfilUsuario(nivel="basico", ferramentas=["python", "git"])
        for cid in CARREIRAS_OBRIGATORIAS:
            analise = analisar_lacunas(self.base, cid, perfil)
            total = len(self.base["carreiras"][cid]["competencias_junior"])
            self.assertEqual(len(analise["declarados"]) + len(analise["lacunas"]), total, cid)
            self.assertEqual(analise["total_competencias"], total)
            self.assertTrue(0 <= analise["cobertura_declarada_percentual"] <= 100)
            ids_d = {c["id"] for c in analise["declarados"]}
            ids_l = {c["id"] for c in analise["lacunas"]}
            self.assertFalse(ids_d & ids_l, cid)

    def test_sem_ferramentas_tudo_e_lacuna_presumida(self):
        analise = analisar_lacunas(self.base, "backend", PerfilUsuario(nivel="iniciante"))
        self.assertEqual(analise["declarados"], [])
        self.assertTrue(all(l["origem"] == ORIGEM_PRESUMIDA for l in analise["lacunas"]))
        self.assertEqual(analise["cobertura_declarada_percentual"], 0)

    def test_conhecimento_declarado_nao_aparece_como_lacuna(self):
        perfil = PerfilUsuario(nivel="intermediario", ferramentas=["sql", "python"])
        analise = analisar_lacunas(self.base, "data_engineering", perfil)
        nomes_lacunas = " ".join(l["nome"] for l in analise["lacunas"])
        self.assertNotIn("SQL", nomes_lacunas.split())
        declarados = {d["id"]: d for d in analise["declarados"]}
        self.assertIn("sql", declarados)
        self.assertEqual(declarados["sql"]["origem"], ORIGEM_DECLARADO)
        self.assertIn("projeto", declarados["sql"]["aprofundamento"])

    def test_lacunas_especificas_da_carreira(self):
        perfil = PerfilUsuario(nivel="basico")
        esperado = {
            "backend": "APIs REST", "frontend": "HTML e CSS", "data_science": "Estatística",
            "data_engineering": "ETL", "security": "Redes", "devops": "Docker", "cloud": "Identidade",
            "mobile": "Navegação", "qa": "Casos de teste", "product": "Descoberta",
        }
        for cid, trecho in esperado.items():
            nomes = " | ".join(l["nome"] for l in analisar_lacunas(self.base, cid, perfil)["lacunas"])
            self.assertIn(trecho, nomes, cid)

    def test_lacunas_essenciais_vem_primeiro(self):
        analise = analisar_lacunas(self.base, "devops", PerfilUsuario())
        prioridades = [l["prioridade"] for l in analise["lacunas"]]
        self.assertEqual(prioridades, sorted(prioridades, key=lambda p: 0 if p == "essencial" else 1))

    def test_carreira_desconhecida(self):
        with self.assertRaises(ValueError):
            analisar_lacunas(self.base, "astronauta", PerfilUsuario())

    def test_ferramentas_invalidas_sao_ignoradas(self):
        analise = analisar_lacunas(self.base, "backend", PerfilUsuario(ferramentas=["nada", None]))
        self.assertEqual(analise["declarados"], [])

    def test_observacao_para_iniciante(self):
        analise = analisar_lacunas(self.base, "qa", PerfilUsuario(nivel="iniciante"))
        self.assertTrue(any("iniciante" in o for o in analise["observacoes"]))


class TestRoadmap(unittest.TestCase):
    def setUp(self):
        self.base = carregar_base()

    def test_roadmap_funciona_para_as_dez_trilhas(self):
        perfil = PerfilUsuario(nivel="basico", ferramentas=["git", "python"])
        for cid in CARREIRAS_OBRIGATORIAS:
            analise = analisar_lacunas(self.base, cid, perfil)
            roadmap = gerar_roadmap(self.base, cid, analise, perfil)
            self.assertEqual([e["chave"] for e in roadmap["etapas"]], [c for c, _ in TITULOS_ETAPAS], cid)
            for etapa in roadmap["etapas"]:
                self.assertTrue(etapa["itens"], f"{cid}:{etapa['chave']}")
                for item in etapa["itens"]:
                    self.assertIn(item["tipo"], ("base", "lacuna", "aprofundamento"))
            self.assertTrue(roadmap["certificacoes"], cid)
            self.assertTrue(roadmap["projeto"]["titulo"], cid)
            self.assertIn("opcionais", roadmap["aviso_certificacoes"])

    def test_lacunas_aparecem_no_roadmap(self):
        perfil = PerfilUsuario(nivel="basico")
        analise = analisar_lacunas(self.base, "backend", perfil)
        roadmap = gerar_roadmap(self.base, "backend", analise, perfil)
        textos = " ".join(i["texto"] for e in roadmap["etapas"] for i in e["itens"] if i["tipo"] == "lacuna")
        self.assertIn("APIs REST", textos)
        self.assertIn("Autenticação", textos)

    def test_declarados_viram_aprofundamento(self):
        perfil = PerfilUsuario(nivel="intermediario", ferramentas=["sql"])
        analise = analisar_lacunas(self.base, "backend", perfil)
        roadmap = gerar_roadmap(self.base, "backend", analise, perfil)
        praticas = next(e for e in roadmap["etapas"] if e["chave"] == "praticas_exercicios")
        self.assertTrue(any(i["tipo"] == "aprofundamento" and "SQL" in i["texto"] for i in praticas["itens"]))

    def test_roadmap_sem_garantias_de_emprego(self):
        perfil = PerfilUsuario()
        analise = analisar_lacunas(self.base, "cloud", perfil)
        roadmap = gerar_roadmap(self.base, "cloud", analise, perfil)
        etapa = roadmap["etapas"][-1]
        self.assertIn("Não há garantia", etapa["descricao"])

    def test_carreira_desconhecida(self):
        with self.assertRaises(ValueError):
            gerar_roadmap(self.base, "xyz", {"lacunas": [], "declarados": []}, PerfilUsuario())

    def test_etapas_do_json_batem_com_o_codigo(self):
        chaves_codigo = {c for c, _ in TITULOS_ETAPAS}
        self.assertTrue(set(ETAPAS_ROADMAP) <= chaves_codigo)


if __name__ == "__main__":
    unittest.main()
