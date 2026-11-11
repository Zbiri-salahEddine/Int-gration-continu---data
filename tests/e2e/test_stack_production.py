"""Vérifie la stack de production déployée : le service traite seul les dépôts S3.

Nécessite DATABASE_URL, S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY et
INTERVALLE_SECONDES pointant vers la stack, sur une base vide.
"""
import time

import psycopg

from pipeline import config, generation, stockage
from tests import valeurs_attendues


def requete(sql):
    with psycopg.connect(config.DATABASE_URL) as connexion:
        return connexion.execute(sql).fetchall()


def attendre_fichiers(nombre, delai_max=60):
    limite = time.monotonic() + delai_max
    while time.monotonic() < limite:
        if requete("SELECT count(*) FROM fichier_traite") == [(nombre,)]:
            return
        time.sleep(1)
    raise AssertionError(f"{nombre} fichiers attendus en base après {delai_max} s")


def test_les_depots_sont_traites_automatiquement_et_une_seule_fois():
    client = stockage.creer_client()
    generation.deposer_csv(client, config.S3_BUCKET)

    attendre_fichiers(valeurs_attendues.NB_FICHIERS)
    valeurs_attendues.verifier_base(requete)

    contenu = stockage.telecharger(client, config.S3_BUCKET, "transactions_2026_01.csv")
    stockage.deposer(client, config.S3_BUCKET, "doublon.csv", contenu)
    time.sleep(3 * config.INTERVALLE_SECONDES)
    valeurs_attendues.verifier_base(requete)
