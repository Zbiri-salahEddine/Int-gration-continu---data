from datetime import datetime
from decimal import Decimal

from pipeline import traitement
from pipeline.modeles import Transaction


def transaction(origine="A", banque="B1", destinataire="C", montant="10.00"):
    return Transaction(
        datetime_transaction=datetime(2026, 1, 1),
        iban_origine=origine,
        pays_source="France",
        banque_source=banque,
        iban_destinataire=destinataire,
        pays_destinataire="France",
        montant=Decimal(montant),
    )


def test_somme_envoyee_par_iban():
    donnees = [transaction("A", montant="10.10"), transaction("A", montant="0.20"), transaction("B", montant="5")]
    assert traitement.somme_envoyee_par_iban(donnees) == {"A": Decimal("10.30"), "B": Decimal("5")}


def test_somme_envoyee_par_banque():
    donnees = [
        transaction(banque="B1", montant="1"),
        transaction(banque="B2", montant="2"),
        transaction(banque="B1", montant="3"),
    ]
    assert traitement.somme_envoyee_par_banque(donnees) == {"B1": Decimal("4"), "B2": Decimal("2")}


def test_somme_recue_par_iban():
    donnees = [transaction(destinataire="X", montant="7"), transaction(destinataire="X", montant="8")]
    assert traitement.somme_recue_par_iban(donnees) == {"X": Decimal("15")}


def test_flag_strictement_au_dessus_du_seuil():
    donnees = [transaction(montant="4999.99"), transaction(montant="5000.00"), transaction(montant="5000.01")]
    resultat = traitement.flagger_transactions(donnees, Decimal("5000"))
    assert [f.flag for f in resultat] == [False, False, True]


def test_traiter_ne_modifie_pas_son_entree():
    donnees = [transaction(), transaction(origine="Z")]
    copie = list(donnees)
    traitement.traiter(donnees, Decimal("5000"))
    assert donnees == copie


def test_meme_entree_meme_sortie():
    donnees = [transaction(montant="6000"), transaction(banque="B9", montant="1")]
    assert traitement.traiter(donnees, Decimal("5000")) == traitement.traiter(donnees, Decimal("5000"))
