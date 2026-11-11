"""Vérifie l'état réel de la base après le passage de la pipeline."""
import base64
import json
import os
import urllib.request

import psycopg

from pipeline import config
from tests import valeurs_attendues
from tests.valeurs_attendues import CARLA, DAVID, D

GRAFANA = os.environ.get("GRAFANA_URL", "http://localhost:3001")


def requete(sql):
    with psycopg.connect(config.DATABASE_URL) as connexion:
        return connexion.execute(sql).fetchall()


def test_les_valeurs_inserees_par_la_pipeline_sont_correctes():
    valeurs_attendues.verifier_base(requete)


def test_une_transaction_est_inseree_a_l_identique():
    ligne = requete(
        "SELECT to_char(datetime_transaction, 'YYYY-MM-DD HH24:MI'), iban_origine, pays_source, "
        "banque_source, iban_destinataire, pays_destinataire, montant, flag "
        "FROM transaction_financiere WHERE montant = 7500.75"
    )
    assert ligne == [
        ("2026-01-07 08:00", CARLA, "Allemagne", "Banque Gamma", DAVID, "Espagne", D("7500.75"), True)
    ]


def test_le_dashboard_lit_les_donnees_de_la_base():
    corps = json.dumps({
        "queries": [{
            "refId": "A", "format": "table", "rawSql": "SELECT count(*) FROM transaction_financiere",
            "datasource": {"type": "postgres", "uid": "transactions-postgres"},
        }],
    }).encode()
    demande = urllib.request.Request(f"{GRAFANA}/api/ds/query", data=corps, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": "Basic " + base64.b64encode(b"admin:admin").decode(),
    })
    with urllib.request.urlopen(demande, timeout=10) as reponse:
        resultat = json.load(reponse)
    assert resultat["results"]["A"]["frames"][0]["data"]["values"] == [[valeurs_attendues.NB_TRANSACTIONS]]
