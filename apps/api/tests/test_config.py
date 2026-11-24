import pytest

from app.core.config import Settings


def test_database_url_has_local_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert (
        s.DATABASE_URL
        == "postgresql://semanticfeed:semanticfeed@localhost:5433/semanticfeed"
    )
    assert s.TEST_DATABASE_URL.endswith("/semanticfeed_test")
