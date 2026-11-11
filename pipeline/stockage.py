"""Accès au stockage S3 local, avec relance des erreurs transitoires."""
from collections.abc import Callable
from typing import TypeVar

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from pipeline import config, retry

T = TypeVar("T")


class ErreurS3Transitoire(Exception):
    """Le service S3 est momentanément indisponible."""


def creer_client():
    return boto3.client(
        "s3",
        endpoint_url=config.S3_ENDPOINT,
        aws_access_key_id=config.S3_ACCESS_KEY,
        aws_secret_access_key=config.S3_SECRET_KEY,
        region_name="us-east-1",
        config=Config(
            s3={"addressing_style": "path"},
            # La relance est gérée ici, pour être visible dans les journaux.
            retries={"max_attempts": 1, "mode": "standard"},
            connect_timeout=3,
            read_timeout=10,
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )


def _appel_s3(operation: Callable[[], T]) -> T:
    try:
        return operation()
    except ClientError as erreur:
        if erreur.response["ResponseMetadata"]["HTTPStatusCode"] >= 500:
            raise ErreurS3Transitoire(str(erreur)) from erreur
        raise
    except BotoCoreError as erreur:
        raise ErreurS3Transitoire(str(erreur)) from erreur


def _avec_relance(operation: Callable[[], T]) -> T:
    return retry.avec_retry(
        lambda: _appel_s3(operation),
        erreurs=(ErreurS3Transitoire,),
        tentatives=config.RETRY_TENTATIVES,
        delai_initial=config.RETRY_DELAI_INITIAL,
    )


def creer_bucket(client, bucket: str) -> None:
    def creer():
        try:
            client.create_bucket(Bucket=bucket)
        except ClientError as erreur:
            if erreur.response["Error"]["Code"] not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                raise
    _avec_relance(creer)


def deposer(client, bucket: str, cle: str, contenu: bytes) -> None:
    _avec_relance(lambda: client.put_object(Bucket=bucket, Key=cle, Body=contenu))


def lister_csv(client, bucket: str) -> list[str]:
    def lister():
        pages = client.get_paginator("list_objects_v2").paginate(Bucket=bucket)
        return sorted(
            objet["Key"] for page in pages for objet in page.get("Contents", [])
            if objet["Key"].endswith(".csv")
        )
    return _avec_relance(lister)


def telecharger(client, bucket: str, cle: str, avant_lecture: Callable[[], None] | None = None) -> bytes:
    def lire():
        if avant_lecture is not None:
            avant_lecture()
        return client.get_object(Bucket=bucket, Key=cle)["Body"].read()
    return _avec_relance(lire)
