"""Service de production : traite régulièrement les nouveaux fichiers du bucket."""
import argparse
import logging
import signal
import sys
import threading
import time

import psycopg
from botocore.exceptions import ClientError

from pipeline import base_donnees, config, execution, stockage

journal = logging.getLogger("planificateur")


def boucle(arret: threading.Event) -> None:
    base_donnees.creer_schema(config.DATABASE_URL, config.SCHEMA_SQL)
    client = stockage.creer_client()
    stockage.creer_bucket(client, config.S3_BUCKET)
    journal.info("Démarré, un cycle toutes les %d s", config.INTERVALLE_SECONDES)

    while not arret.is_set():
        try:
            bilan = execution.traiter_bucket(client, config.S3_BUCKET, config.DATABASE_URL)
        except (stockage.ErreurS3Transitoire, ClientError, psycopg.Error) as erreur:
            journal.error("Cycle en échec : %s", erreur)
        else:
            config.FICHIER_BATTEMENT.touch()
            journal.info(
                "Cycle terminé : %d insérés, %d ignorés, %d en échec",
                len(bilan["insere"]), len(bilan["ignore"]), len(bilan["echec"]),
            )
        arret.wait(config.INTERVALLE_SECONDES)
    journal.info("Arrêt demandé, fin du service")


def est_en_bonne_sante() -> bool:
    """Le service est sain si un cycle a réussi récemment."""
    try:
        age = time.time() - config.FICHIER_BATTEMENT.stat().st_mtime
    except FileNotFoundError:
        return False
    return age < 3 * config.INTERVALLE_SECONDES + 30


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--sante", action="store_true", help="vérifie le battement du service")
    if parseur.parse_args().sante:
        sys.exit(0 if est_en_bonne_sante() else 1)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
    arret = threading.Event()
    for signal_arret in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signal_arret, lambda *_: arret.set())
    boucle(arret)


if __name__ == "__main__":
    main()
