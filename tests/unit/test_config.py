import pytest

from payments.config import database_url

ALL_VARS = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")


@pytest.fixture
def db_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Start every test from a known environment: all required vars set, no port."""
    for name in ALL_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DB_HOST", "db.example")
    monkeypatch.setenv("DB_NAME", "ledger")
    monkeypatch.setenv("DB_USER", "ledger")
    monkeypatch.setenv("DB_PASSWORD", "secret")
    return monkeypatch


def test_builds_url_from_parts(db_env: pytest.MonkeyPatch) -> None:
    url = database_url()

    assert url.drivername == "postgresql+asyncpg"
    assert url.host == "db.example"
    assert url.database == "ledger"
    assert url.username == "ledger"
    assert url.password == "secret"


def test_port_defaults_to_5432(db_env: pytest.MonkeyPatch) -> None:
    assert database_url().port == 5432


def test_explicit_port_is_used(db_env: pytest.MonkeyPatch) -> None:
    db_env.setenv("DB_PORT", "5433")

    assert database_url().port == 5433


def test_special_characters_in_password_survive(db_env: pytest.MonkeyPatch) -> None:
    db_env.setenv("DB_PASSWORD", "p@ss/w:rd")

    url = database_url()

    assert url.host == "db.example"
    assert url.password == "p@ss/w:rd"
    assert "p%40ss%2Fw%3Ard" in url.render_as_string(hide_password=False)


def test_missing_vars_are_all_named(db_env: pytest.MonkeyPatch) -> None:
    db_env.delenv("DB_HOST")
    db_env.setenv("DB_PASSWORD", "")

    with pytest.raises(RuntimeError, match="missing DB_HOST, DB_PASSWORD;"):
        database_url()
