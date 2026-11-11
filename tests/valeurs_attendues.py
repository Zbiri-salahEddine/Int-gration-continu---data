"""Résultats attendus, calculés à la main à partir des 20 transactions générées.

Ces valeurs ne réutilisent volontairement pas le code de traitement.
"""
from decimal import Decimal as D

ALICE = "FR7630001007941234567890185"
BRUNO = "FR7630004000031234567890143"
CARLA = "DE89370400440532013000"
DAVID = "ES9121000418450200051332"
EMMA = "IT60X0542811101000000123456"

NB_FICHIERS = 3
NB_TRANSACTIONS = 20

ENVOYE_PAR_IBAN = {
    ALICE: D("10460.75"),
    BRUNO: D("2828.80"),
    CARLA: D("10821.45"),
    DAVID: D("17133.31"),
    EMMA: D("11275.91"),
}
ENVOYE_PAR_BANQUE = {
    "Banque Alpha": D("10460.75"),
    "Banque Beta": D("2828.80"),
    "Banque Gamma": D("10821.45"),
    "Banque Delta": D("17133.31"),
    "Banque Epsilon": D("11275.91"),
}
RECU_PAR_IBAN = {
    ALICE: D("8490.60"),
    BRUNO: D("12820.99"),
    CARLA: D("6318.83"),
    DAVID: D("12400.75"),
    EMMA: D("12489.05"),
}
MONTANTS_FLAGGES = [D("5000.01"), D("6200.40"), D("7500.75"), D("12000.00")]


def verifier_base(requete) -> None:
    """Vérifie l'état complet d'une base après traitement des 3 fichiers."""
    assert requete("SELECT count(*) FROM fichier_traite") == [(NB_FICHIERS,)]
    assert requete("SELECT count(*) FROM transaction_financiere") == [(NB_TRANSACTIONS,)]
    assert dict(requete("SELECT iban, total FROM total_envoye_par_iban")) == ENVOYE_PAR_IBAN
    assert dict(requete("SELECT banque, total FROM total_envoye_par_banque")) == ENVOYE_PAR_BANQUE
    assert dict(requete("SELECT iban, total FROM total_recu_par_iban")) == RECU_PAR_IBAN
    flaggees = requete("SELECT montant FROM transaction_financiere WHERE flag ORDER BY montant")
    assert [ligne[0] for ligne in flaggees] == MONTANTS_FLAGGES
