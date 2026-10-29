"""Funções auxiliares compartilhadas pelos testes."""
import copy

from carreiras.base_conhecimento import carregar_base


def base_copia():
    """Carrega a base real e devolve uma cópia independente para ser alterada nos testes."""
    return copy.deepcopy(carregar_base())


def respostas_iguais(valor, base=None):
    base = base or carregar_base()
    return {d["id"]: valor for d in base["dimensoes"]}
