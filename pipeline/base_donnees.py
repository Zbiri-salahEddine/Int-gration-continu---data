"""Accès à PostgreSQL : création du schéma et insertion des résultats."""
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import psycopg

from pipeline.modeles import ResultatTraitement


def _connecter(url: str) -> psycopg.Connection:
    return psycopg.connect(url, connect_timeout=5)


def creer_schema(url: str, schema: Path) -> None:
    with _connecter(url) as connexion:
        connexion.execute(schema.read_text(encoding="utf-8"))


def fichier_deja_traite(url: str, empreinte: str) -> bool:
    with _connecter(url) as connexion:
        ligne = connexion.execute(
            "SELECT 1 FROM fichier_traite WHERE empreinte = %s", (empreinte,)
        ).fetchone()
    return ligne is not None


def _ajouter_totaux(curseur, table: str, colonne: str, totaux: dict[str, Decimal]) -> None:
    # Les totaux s'accumulent d'un fichier à l'autre.
    curseur.executemany(
        f"INSERT INTO {table} ({colonne}, total) VALUES (%s, %s) "
        f"ON CONFLICT ({colonne}) DO UPDATE SET total = {table}.total + EXCLUDED.total",
        list(totaux.items()),
    )


def inserer_resultat(
    url: str,
    nom: str,
    empreinte: str,
    resultat: ResultatTraitement,
    avant_commit: Callable[[], None] | None = None,
) -> bool:
    """Insère un fichier en une seule transaction SQL.

    Le fichier est enregistré dans la même transaction que ses données : soit
    tout est validé, soit rien ne l'est, et une relance ne peut pas créer de
    doublon. Retourne False si le fichier avait déjà été inséré.
    """
    with _connecter(url) as connexion, connexion.cursor() as curseur:
        curseur.execute(
            "INSERT INTO fichier_traite (nom, empreinte, nb_lignes) VALUES (%s, %s, %s) "
            "ON CONFLICT (empreinte) DO NOTHING RETURNING id",
            (nom, empreinte, len(resultat.transactions)),
        )
        ligne = curseur.fetchone()
        if ligne is None:
            return False
        fichier_id = ligne[0]

        curseur.executemany(
            "INSERT INTO transaction_financiere (fichier_id, numero_ligne, "
            "datetime_transaction, iban_origine, pays_source, banque_source, "
            "iban_destinataire, pays_destinataire, montant, flag) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    fichier_id, numero, f.transaction.datetime_transaction,
                    f.transaction.iban_origine, f.transaction.pays_source,
                    f.transaction.banque_source, f.transaction.iban_destinataire,
                    f.transaction.pays_destinataire, f.transaction.montant, f.flag,
                )
                for numero, f in enumerate(resultat.transactions, start=1)
            ],
        )
        _ajouter_totaux(curseur, "total_envoye_par_iban", "iban", resultat.envoye_par_iban)
        _ajouter_totaux(curseur, "total_envoye_par_banque", "banque", resultat.envoye_par_banque)
        _ajouter_totaux(curseur, "total_recu_par_iban", "iban", resultat.recu_par_iban)

        if avant_commit is not None:
            avant_commit()
    return True
