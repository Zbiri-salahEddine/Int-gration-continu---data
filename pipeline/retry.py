"""Relance d'une opération après une erreur transitoire."""
import logging
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")
journal = logging.getLogger(__name__)


def avec_retry(
    operation: Callable[[], T],
    erreurs: tuple[type[Exception], ...],
    tentatives: int,
    delai_initial: float,
    attendre: Callable[[float], None] = time.sleep,
) -> T:
    """Exécute `operation`, avec un délai doublé entre chaque tentative.

    Seules les `erreurs` listées sont relancées ; les autres remontent aussitôt.
    La dernière erreur remonte si toutes les tentatives échouent.
    """
    if tentatives < 1:
        raise ValueError("tentatives doit être supérieur ou égal à 1")
    delai = delai_initial
    for tentative in range(1, tentatives):
        try:
            return operation()
        except erreurs as erreur:
            journal.warning(
                "Tentative %d/%d échouée (%s), nouvel essai dans %.1fs",
                tentative, tentatives, erreur, delai,
            )
            attendre(delai)
            delai *= 2
    return operation()
