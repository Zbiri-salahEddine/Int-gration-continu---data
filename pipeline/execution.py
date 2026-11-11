"""Enchaîne téléchargement, traitement et insertion, fichier par fichier."""
import logging
from collections.abc import Callable

import psycopg
from botocore.exceptions import ClientError

from pipeline import base_donnees, chargement, config, retry, stockage, traitement

journal = logging.getLogger(__name__)


class PanneSimulee:
    """Lève `erreur` lors des `n` premiers appels."""

    def __init__(self, n: int, erreur: Exception):
        self.restantes = n
        self.erreur = erreur

    def __call__(self) -> None:
        if self.restantes > 0:
            self.restantes -= 1
            raise self.erreur


def _relancer_bd(operation):
    return retry.avec_retry(
        operation,
        erreurs=(psycopg.OperationalError,),
        tentatives=config.RETRY_TENTATIVES,
        delai_initial=config.RETRY_DELAI_INITIAL,
    )


def traiter_objet(
    client,
    bucket: str,
    cle: str,
    url: str,
    avant_lecture: Callable[[], None] | None = None,
    avant_commit: Callable[[], None] | None = None,
) -> str:
    """Traite un CSV du bucket et retourne 'insere' ou 'ignore'."""
    contenu = stockage.telecharger(client, bucket, cle, avant_lecture)
    empreinte = chargement.empreinte(contenu)
    if _relancer_bd(lambda: base_donnees.fichier_deja_traite(url, empreinte)):
        journal.info("%s : déjà traité, ignoré", cle)
        return "ignore"

    transactions = chargement.analyser_csv(contenu)
    resultat = traitement.traiter(transactions, config.SEUIL_FLAG)
    insere = _relancer_bd(
        lambda: base_donnees.inserer_resultat(url, cle, empreinte, resultat, avant_commit)
    )
    if not insere:
        journal.info("%s : déjà traité, ignoré", cle)
        return "ignore"
    journal.info("%s : %d transactions insérées", cle, len(transactions))
    return "insere"


def traiter_bucket(
    client,
    bucket: str,
    url: str,
    avant_lecture: Callable[[], None] | None = None,
    avant_commit: Callable[[], None] | None = None,
) -> dict[str, list[str]]:
    """Traite chaque CSV ; une erreur n'empêche pas de traiter les suivants."""
    bilan: dict[str, list[str]] = {"insere": [], "ignore": [], "echec": []}
    for cle in stockage.lister_csv(client, bucket):
        try:
            statut = traiter_objet(client, bucket, cle, url, avant_lecture, avant_commit)
        except (chargement.FichierInvalide, stockage.ErreurS3Transitoire, ClientError, psycopg.Error) as erreur:
            journal.error("%s : ÉCHEC : %s", cle, erreur)
            statut = "echec"
        bilan[statut].append(cle)
    return bilan
