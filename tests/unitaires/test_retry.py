import pytest

from pipeline.retry import avec_retry


class Operation:
    def __init__(self, echecs, erreur=ConnectionError):
        self.echecs, self.erreur, self.appels = echecs, erreur, 0

    def __call__(self):
        self.appels += 1
        if self.appels <= self.echecs:
            raise self.erreur("panne")
        return "ok"


def lancer(operation, tentatives=4, delais=None):
    attendre = (delais if delais is not None else []).append
    return avec_retry(operation, (ConnectionError,), tentatives, 0.5, attendre)


def test_reussit_apres_des_pannes_avec_delai_exponentiel():
    operation, delais = Operation(2), []
    assert lancer(operation, delais=delais) == "ok"
    assert operation.appels == 3
    assert delais == [0.5, 1.0]


def test_abandonne_apres_le_nombre_maximal():
    operation = Operation(10)
    with pytest.raises(ConnectionError):
        lancer(operation, tentatives=3)
    assert operation.appels == 3


def test_ne_relance_pas_une_erreur_non_transitoire():
    operation = Operation(1, erreur=ValueError)
    with pytest.raises(ValueError):
        lancer(operation)
    assert operation.appels == 1
