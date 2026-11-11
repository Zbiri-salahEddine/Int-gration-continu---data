"""Traitements métier : uniquement des fonctions pures, sans entrée/sortie."""
from collections.abc import Callable, Iterable
from decimal import Decimal

from pipeline.modeles import ResultatTraitement, Transaction, TransactionFlaggee


def _somme_par(
    transactions: Iterable[Transaction], cle: Callable[[Transaction], str]
) -> dict[str, Decimal]:
    totaux: dict[str, Decimal] = {}
    for transaction in transactions:
        valeur = cle(transaction)
        totaux[valeur] = totaux.get(valeur, Decimal("0")) + transaction.montant
    return totaux


def somme_envoyee_par_iban(transactions: Iterable[Transaction]) -> dict[str, Decimal]:
    return _somme_par(transactions, lambda t: t.iban_origine)


def somme_envoyee_par_banque(transactions: Iterable[Transaction]) -> dict[str, Decimal]:
    return _somme_par(transactions, lambda t: t.banque_source)


def somme_recue_par_iban(transactions: Iterable[Transaction]) -> dict[str, Decimal]:
    return _somme_par(transactions, lambda t: t.iban_destinataire)


def flagger_transactions(
    transactions: Iterable[Transaction], seuil: Decimal
) -> list[TransactionFlaggee]:
    """Flag les transactions strictement au-dessus du seuil."""
    return [TransactionFlaggee(t, t.montant > seuil) for t in transactions]


def traiter(transactions: list[Transaction], seuil: Decimal) -> ResultatTraitement:
    return ResultatTraitement(
        envoye_par_iban=somme_envoyee_par_iban(transactions),
        envoye_par_banque=somme_envoyee_par_banque(transactions),
        recu_par_iban=somme_recue_par_iban(transactions),
        transactions=flagger_transactions(transactions, seuil),
    )
