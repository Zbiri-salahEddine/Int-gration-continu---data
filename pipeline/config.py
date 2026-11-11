"""Configuration lue depuis l'environnement, avec des valeurs de développement."""
import os
from decimal import Decimal
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCHEMA_SQL = RACINE / "sql" / "schema.sql"

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://pipeline:pipeline@localhost:5433/transactions"
)

S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://localhost:8333")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "pipeline-dev")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "pipeline-dev-secret")
S3_BUCKET = os.environ.get("S3_BUCKET", "transactions")

SEUIL_FLAG = Decimal("5000")

RETRY_TENTATIVES = int(os.environ.get("RETRY_TENTATIVES", "4"))
RETRY_DELAI_INITIAL = float(os.environ.get("RETRY_DELAI_INITIAL", "0.5"))

INTERVALLE_SECONDES = int(os.environ.get("INTERVALLE_SECONDES", "30"))
FICHIER_BATTEMENT = Path(os.environ.get("FICHIER_BATTEMENT", "/tmp/pipeline-battement"))
