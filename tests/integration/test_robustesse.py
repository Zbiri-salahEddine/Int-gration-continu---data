"""Idempotence et reprise sur panne, contre un vrai S3 et un vrai PostgreSQL."""
import psycopg
import pytest

from pipeline import execution, stockage
from tests import valeurs_attendues
from tests.integration.conftest import BUCKET_TEST

JANVIER = "transactions_2026_01.csv"
FEVRIER = "transactions_2026_02.csv"


def panne_insertion(n):
    return execution.PanneSimulee(n, psycopg.OperationalError("panne d'insertion simulée"))


def panne_telechargement(n):
    return execution.PanneSimulee(n, stockage.ErreurS3Transitoire("panne de téléchargement simulée"))


def test_les_trois_fichiers_sont_inseres(client, url, requete):
    bilan = execution.traiter_bucket(client, BUCKET_TEST, url)
    assert len(bilan["insere"]) == 3 and not bilan["echec"]
    valeurs_attendues.verifier_base(requete)


def test_un_fichier_n_est_jamais_traite_deux_fois(client, url, requete):
    execution.traiter_bucket(client, BUCKET_TEST, url)
    bilan = execution.traiter_bucket(client, BUCKET_TEST, url)
    assert len(bilan["ignore"]) == 3 and not bilan["insere"]
    valeurs_attendues.verifier_base(requete)


def test_un_fichier_renomme_n_est_pas_retraite(client, url, requete):
    execution.traiter_bucket(client, BUCKET_TEST, url)
    contenu = stockage.telecharger(client, BUCKET_TEST, JANVIER)
    stockage.deposer(client, BUCKET_TEST, "copie_renommee.csv", contenu)

    bilan = execution.traiter_bucket(client, BUCKET_TEST, url)

    assert "copie_renommee.csv" in bilan["ignore"]
    valeurs_attendues.verifier_base(requete)


def test_les_pannes_d_insertion_sont_relancees_sans_doublon(client, url, requete):
    panne = panne_insertion(2)
    bilan = execution.traiter_bucket(client, BUCKET_TEST, url, avant_commit=panne)
    assert panne.restantes == 0
    assert len(bilan["insere"]) == 3 and not bilan["echec"]
    valeurs_attendues.verifier_base(requete)


def test_un_echec_definitif_d_insertion_ne_laisse_rien_puis_le_fichier_est_repris(client, url, requete):
    with pytest.raises(psycopg.OperationalError):
        execution.traiter_objet(client, BUCKET_TEST, JANVIER, url, avant_commit=panne_insertion(99))

    for table in ("fichier_traite", "transaction_financiere", "total_envoye_par_iban",
                  "total_envoye_par_banque", "total_recu_par_iban"):
        assert requete(f"SELECT count(*) FROM {table}") == [(0,)]

    assert execution.traiter_objet(client, BUCKET_TEST, JANVIER, url) == "insere"
    assert requete("SELECT count(*) FROM transaction_financiere") == [(5,)]


def test_les_pannes_de_telechargement_sont_relancees(client, url, requete):
    panne = panne_telechargement(3)
    bilan = execution.traiter_bucket(client, BUCKET_TEST, url, avant_lecture=panne)
    assert panne.restantes == 0
    assert len(bilan["insere"]) == 3 and not bilan["echec"]
    valeurs_attendues.verifier_base(requete)


def test_un_telechargement_definitivement_en_panne_est_repris_au_passage_suivant(client, url, requete):
    bilan = execution.traiter_bucket(client, BUCKET_TEST, url, avant_lecture=panne_telechargement(99))
    assert len(bilan["echec"]) == 3
    assert requete("SELECT count(*) FROM fichier_traite") == [(0,)]

    bilan = execution.traiter_bucket(client, BUCKET_TEST, url)
    assert len(bilan["insere"]) == 3
    valeurs_attendues.verifier_base(requete)


def test_un_fichier_invalide_est_signale_sans_bloquer_les_autres(client, url, requete):
    stockage.deposer(client, BUCKET_TEST, FEVRIER, b"mauvais,format\n1,2\n")

    bilan = execution.traiter_bucket(client, BUCKET_TEST, url)

    assert bilan["echec"] == [FEVRIER]
    assert len(bilan["insere"]) == 2
    assert requete("SELECT count(*) FROM transaction_financiere") == [(13,)]
