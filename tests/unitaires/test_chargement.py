from decimal import Decimal

import pytest

from pipeline import chargement
from pipeline.generation import COLONNES, construire_csv

ENTETE = ",".join(COLONNES)
VALIDE = "2026-01-05T09:15:00,FR7630001007941234567890185,France,Alpha,DE89370400440532013000,Allemagne,12.50"


def csv_octets(*lignes):
    return "\n".join((ENTETE, *lignes)).encode()


def test_ligne_valide():
    [transaction] = chargement.analyser_csv(csv_octets(VALIDE))
    assert transaction.montant == Decimal("12.50")
    assert transaction.banque_source == "Alpha"


@pytest.mark.parametrize("ancien, nouveau, message", [
    ("12.50", '"12,50"', "montant"),
    ("12.50", "-3", "positif"),
    ("12.50", "NaN", "positif"),
    ("FR7630001007941234567890185", "PAS-UN-IBAN", "iban_origine"),
    ("2026-01-05T09:15:00", "hier", "date"),
    ("France", "", "pays_source"),
])
def test_valeur_invalide(ancien, nouveau, message):
    with pytest.raises(chargement.FichierInvalide, match=message):
        chargement.analyser_csv(csv_octets(VALIDE.replace(ancien, nouveau, 1)))


def test_colonnes_incorrectes():
    with pytest.raises(chargement.FichierInvalide, match="colonnes"):
        chargement.analyser_csv(b"a,b\n1,2\n")


def test_ligne_tronquee():
    with pytest.raises(chargement.FichierInvalide, match="nombre de colonnes"):
        chargement.analyser_csv(csv_octets("2026-01-05T09:15:00,FR76"))


def test_fichier_sans_transaction():
    with pytest.raises(chargement.FichierInvalide, match="aucune"):
        chargement.analyser_csv(csv_octets())


def test_empreinte_depend_uniquement_du_contenu():
    assert chargement.empreinte(b"abc") == chargement.empreinte(b"abc")
    assert chargement.empreinte(b"abc") != chargement.empreinte(b"abd")


def test_generation_deterministe_et_conforme():
    fichiers = construire_csv()
    assert fichiers == construire_csv()
    assert len(fichiers) >= 2
    for contenu in fichiers.values():
        assert 5 <= len(chargement.analyser_csv(contenu)) <= 10
