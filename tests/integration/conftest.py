"""Base et bucket dédiés aux tests de robustesse.

Ils sont séparés de ceux de la pipeline, dont le résultat reste intact.
"""
import psycopg
import pytest
from psycopg import conninfo

from pipeline import base_donnees, config, generation, stockage

BASE_TEST = "transactions_test"
BUCKET_TEST = "transactions-test"


@pytest.fixture(scope="session")
def url_session():
    with psycopg.connect(config.DATABASE_URL, autocommit=True) as connexion:
        connexion.execute(f"DROP DATABASE IF EXISTS {BASE_TEST} WITH (FORCE)")
        connexion.execute(f"CREATE DATABASE {BASE_TEST}")
    url = conninfo.make_conninfo(config.DATABASE_URL, dbname=BASE_TEST)
    base_donnees.creer_schema(url, config.SCHEMA_SQL)
    return url


@pytest.fixture
def url(url_session):
    with psycopg.connect(url_session) as connexion:
        connexion.execute(
            "TRUNCATE fichier_traite, transaction_financiere, total_envoye_par_iban, "
            "total_envoye_par_banque, total_recu_par_iban RESTART IDENTITY"
        )
    return url_session


@pytest.fixture
def client():
    """Client S3 sur un bucket vide contenant ensuite les CSV de référence."""
    client = stockage.creer_client()
    stockage.creer_bucket(client, BUCKET_TEST)
    for cle in stockage.lister_csv(client, BUCKET_TEST):
        client.delete_object(Bucket=BUCKET_TEST, Key=cle)
    generation.deposer_csv(client, BUCKET_TEST)
    return client


@pytest.fixture
def requete(url):
    def executer(sql):
        with psycopg.connect(url) as connexion:
            return connexion.execute(sql).fetchall()
    return executer
