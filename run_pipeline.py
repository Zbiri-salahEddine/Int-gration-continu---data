"""Pipeline complète, ou une seule de ses étapes.

    python run_pipeline.py                 # toutes les étapes
    python run_pipeline.py generation      # une seule étape

Le workflow GitHub Actions appelle ces mêmes étapes une par une.
"""
import argparse
import logging
import subprocess
import sys

import psycopg

from pipeline import base_donnees, config, execution, generation, stockage

journal = logging.getLogger("pipeline")


def etape_infra() -> None:
    subprocess.run(["docker", "compose", "up", "-d", "--wait"], cwd=config.RACINE, check=True)
    stockage.creer_bucket(stockage.creer_client(), config.S3_BUCKET)
    journal.info("S3, PostgreSQL et Grafana démarrés, bucket %s prêt", config.S3_BUCKET)


def etape_generation() -> None:
    cles = generation.deposer_csv(stockage.creer_client(), config.S3_BUCKET)
    journal.info("%d fichiers CSV déposés dans s3://%s", len(cles), config.S3_BUCKET)


def etape_base() -> None:
    base_donnees.creer_schema(config.DATABASE_URL, config.SCHEMA_SQL)
    journal.info("Schéma de la base créé")


def etape_traitement(pannes_telechargement: int, pannes_insertion: int) -> None:
    bilan = execution.traiter_bucket(
        stockage.creer_client(),
        config.S3_BUCKET,
        config.DATABASE_URL,
        avant_lecture=execution.PanneSimulee(
            pannes_telechargement, stockage.ErreurS3Transitoire("panne de téléchargement simulée")
        ),
        avant_commit=execution.PanneSimulee(
            pannes_insertion, psycopg.OperationalError("panne d'insertion simulée")
        ),
    )
    journal.info(
        "Bilan : %d insérés, %d ignorés, %d en échec",
        len(bilan["insere"]), len(bilan["ignore"]), len(bilan["echec"]),
    )
    if bilan["echec"]:
        sys.exit(f"Fichiers en échec : {', '.join(bilan['echec'])}")


def etape_tests_integration() -> None:
    subprocess.run([sys.executable, "-m", "pytest", "tests/integration", "-v"], cwd=config.RACINE, check=True)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
    parseur = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parseur.add_argument(
        "etape", nargs="?", default="tout",
        choices=["tout", "infra", "generation", "base", "traitement", "tests-integration"],
    )
    parseur.add_argument(
        "--simuler-pannes-insertion", type=int, default=0, metavar="N",
        help="fait échouer les N premières insertions, pour démontrer le retry",
    )
    parseur.add_argument(
        "--simuler-pannes-telechargement", type=int, default=0, metavar="N",
        help="fait échouer les N premiers téléchargements, pour démontrer le retry",
    )
    args = parseur.parse_args()

    etapes = {
        "infra": etape_infra,
        "generation": etape_generation,
        "base": etape_base,
        "traitement": lambda: etape_traitement(
            args.simuler_pannes_telechargement, args.simuler_pannes_insertion
        ),
        "tests-integration": etape_tests_integration,
    }
    for nom, etape in etapes.items():
        if args.etape in ("tout", nom):
            journal.info("=== Étape : %s ===", nom)
            try:
                etape()
            except subprocess.CalledProcessError as erreur:
                sys.exit(f"Étape {nom} en échec (code {erreur.returncode})")


if __name__ == "__main__":
    main()
