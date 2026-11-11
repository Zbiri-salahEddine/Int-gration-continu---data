"""Structures de données partagées par le chargement et le traitement."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Transaction:
    datetime_transaction: datetime
    iban_origine: str
    pays_source: str
    banque_source: str
    iban_destinataire: str
    pays_destinataire: str
    montant: Decimal


@dataclass(frozen=True)
class TransactionFlaggee:
    transaction: Transaction
    flag: bool


@dataclass(frozen=True)
class ResultatTraitement:
    envoye_par_iban: dict[str, Decimal]
    envoye_par_banque: dict[str, Decimal]
    recu_par_iban: dict[str, Decimal]
    transactions: list[TransactionFlaggee]
