"""Génère des CSV de transactions à partir de données fixes et les dépose dans S3.

Les données ne sont pas aléatoires : les tests d'intégration comparent la base
à des totaux calculés à la main sur ce jeu de données.
"""
import csv
import io

from pipeline import stockage

COLONNES = [
    "datetime_transaction",
    "iban_origine",
    "pays_source",
    "banque_source",
    "iban_destinataire",
    "pays_destinataire",
    "montant",
]

ALICE = "FR7630001007941234567890185"
BRUNO = "FR7630004000031234567890143"
CARLA = "DE89370400440532013000"
DAVID = "ES9121000418450200051332"
EMMA = "IT60X0542811101000000123456"

FICHIERS = {
    "transactions_2026_01.csv": [
        ("2026-01-05T09:15:00", ALICE, "France", "Banque Alpha", BRUNO, "France", "1200.50"),
        ("2026-01-05T10:30:00", BRUNO, "France", "Banque Beta", CARLA, "Allemagne", "300.00"),
        ("2026-01-06T14:45:00", ALICE, "France", "Banque Alpha", CARLA, "Allemagne", "5000.00"),
        ("2026-01-07T08:00:00", CARLA, "Allemagne", "Banque Gamma", DAVID, "Espagne", "7500.75"),
        ("2026-01-08T16:20:00", DAVID, "Espagne", "Banque Delta", ALICE, "France", "99.99"),
    ],
    "transactions_2026_02.csv": [
        ("2026-02-02T11:00:00", EMMA, "Italie", "Banque Epsilon", ALICE, "France", "5000.01"),
        ("2026-02-03T09:10:00", ALICE, "France", "Banque Alpha", EMMA, "Italie", "250.25"),
        ("2026-02-04T13:30:00", BRUNO, "France", "Banque Beta", DAVID, "Espagne", "1800.00"),
        ("2026-02-05T15:45:00", CARLA, "Allemagne", "Banque Gamma", BRUNO, "France", "420.10"),
        ("2026-02-06T17:05:00", DAVID, "Espagne", "Banque Delta", EMMA, "Italie", "12000.00"),
        ("2026-02-09T08:25:00", EMMA, "Italie", "Banque Epsilon", CARLA, "Allemagne", "75.50"),
        ("2026-02-10T10:40:00", BRUNO, "France", "Banque Beta", ALICE, "France", "640.00"),
    ],
    "transactions_2026_03.csv": [
        ("2026-03-02T09:00:00", ALICE, "France", "Banque Alpha", DAVID, "Espagne", "3100.00"),
        ("2026-03-03T10:15:00", CARLA, "Allemagne", "Banque Gamma", EMMA, "Italie", "150.00"),
        ("2026-03-04T11:30:00", DAVID, "Espagne", "Banque Delta", BRUNO, "France", "4999.99"),
        ("2026-03-05T12:45:00", EMMA, "Italie", "Banque Epsilon", BRUNO, "France", "6200.40"),
        ("2026-03-06T14:00:00", BRUNO, "France", "Banque Beta", EMMA, "Italie", "88.80"),
        ("2026-03-09T15:15:00", ALICE, "France", "Banque Alpha", CARLA, "Allemagne", "910.00"),
        ("2026-03-10T16:30:00", CARLA, "Allemagne", "Banque Gamma", ALICE, "France", "2750.60"),
        ("2026-03-11T17:45:00", DAVID, "Espagne", "Banque Delta", CARLA, "Allemagne", "33.33"),
    ],
}


def construire_csv() -> dict[str, bytes]:
    """Retourne le contenu de chaque CSV, indexé par nom de fichier."""
    fichiers = {}
    for nom, lignes in FICHIERS.items():
        tampon = io.StringIO()
        ecrivain = csv.writer(tampon, lineterminator="\n")
        ecrivain.writerow(COLONNES)
        ecrivain.writerows(lignes)
        fichiers[nom] = tampon.getvalue().encode("utf-8")
    return fichiers


def deposer_csv(client, bucket: str) -> list[str]:
    """Dépose les CSV dans le bucket et retourne leurs clés."""
    fichiers = construire_csv()
    for nom, contenu in fichiers.items():
        stockage.deposer(client, bucket, nom, contenu)
    return list(fichiers)
