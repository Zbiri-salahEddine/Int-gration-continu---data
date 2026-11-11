import pytest

from pipeline import config


@pytest.fixture(autouse=True)
def retry_rapide(monkeypatch):
    monkeypatch.setattr(config, "RETRY_DELAI_INITIAL", 0.01)
