import io

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from pipeline import stockage


def erreur_client(code, statut):
    return ClientError(
        {"Error": {"Code": code, "Message": code}, "ResponseMetadata": {"HTTPStatusCode": statut}},
        "GetObject",
    )


class ClientFactice:
    def __init__(self, *erreurs):
        self.erreurs = list(erreurs)
        self.appels = 0

    def get_object(self, Bucket, Key):
        self.appels += 1
        if self.erreurs:
            raise self.erreurs.pop(0)
        return {"Body": io.BytesIO(b"contenu")}


def test_reprend_apres_des_erreurs_transitoires():
    client = ClientFactice(EndpointConnectionError(endpoint_url="http://s3"), erreur_client("SlowDown", 503))
    assert stockage.telecharger(client, "b", "c") == b"contenu"
    assert client.appels == 3


def test_abandonne_apres_le_nombre_maximal():
    client = ClientFactice(*[erreur_client("InternalError", 500) for _ in range(10)])
    with pytest.raises(stockage.ErreurS3Transitoire):
        stockage.telecharger(client, "b", "c")
    assert client.appels == 4


def test_ne_relance_pas_un_objet_inexistant():
    client = ClientFactice(erreur_client("NoSuchKey", 404))
    with pytest.raises(ClientError):
        stockage.telecharger(client, "b", "c")
    assert client.appels == 1
