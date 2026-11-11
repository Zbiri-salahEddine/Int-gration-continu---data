"""Chargement des données : validation des CSV récupérés depuis S3."""
import csv
import hashlib
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from pipeline.generation import COLONNES
from pipeline.modeles import Transaction

FORMAT_IBAN = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$")


class FichierInvalide(Exception):
    """Le contenu d'un CSV ne respecte pas le format attendu."""


def empreinte(contenu: bytes) -> str:
    """Identifie un fichier par son contenu, même s'il est renommé."""
    return hashlib.sha256(contenu).hexdigest()


def _ligne_vers_transaction(ligne: dict[str, str], numero: int) -> Transaction:
    for colonne in ("iban_origine", "iban_destinataire"):
        if not FORMAT_IBAN.match(ligne[colonne]):
            raise FichierInvalide(f"ligne {numero} : {colonne} invalide ({ligne[colonne]!r})")
    for colonne in ("pays_source", "banque_source", "pays_destinataire"):
        if not ligne[colonne].strip():
            raise FichierInvalide(f"ligne {numero} : {colonne} vide")
    try:
        date = datetime.fromisoformat(ligne["datetime_transaction"])
    except ValueError as erreur:
        raise FichierInvalide(f"ligne {numero} : date invalide ({erreur})") from erreur
    try:
        montant = Decimal(ligne["montant"])
    except InvalidOperation as erreur:
        raise FichierInvalide(f"ligne {numero} : montant invalide ({ligne['montant']!r})") from erreur
    if not montant.is_finite() or montant <= 0:
        raise FichierInvalide(f"ligne {numero} : le montant doit être positif ({montant})")
    return Transaction(
        datetime_transaction=date,
        iban_origine=ligne["iban_origine"],
        pays_source=ligne["pays_source"],
        banque_source=ligne["banque_source"],
        iban_destinataire=ligne["iban_destinataire"],
        pays_destinataire=ligne["pays_destinataire"],
        montant=montant,
    )


def analyser_csv(contenu: bytes) -> list[Transaction]:
    """Convertit le contenu d'un CSV en transactions validées."""
    try:
        texte = contenu.decode("utf-8")
    except UnicodeDecodeError as erreur:
        raise FichierInvalide(f"encodage invalide : {erreur}") from erreur
    lecteur = csv.DictReader(io.StringIO(texte))
    if lecteur.fieldnames != COLONNES:
        raise FichierInvalide(f"colonnes attendues {COLONNES}, reçues {lecteur.fieldnames}")
    transactions = []
    for numero, ligne in enumerate(lecteur, start=2):
        if None in ligne or None in ligne.values():
            raise FichierInvalide(f"ligne {numero} : nombre de colonnes incorrect")
        transactions.append(_ligne_vers_transaction(ligne, numero))
    if not transactions:
        raise FichierInvalide("le fichier ne contient aucune transaction")
    return transactions
