from datetime import date

import pytest
from sqlalchemy import Engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.paper import Paper


def _paper(doi: str) -> Paper:
    return Paper(
        doi=doi,
        version=1,
        title="Place cells",
        abstract="Hippocampal replay.",
        authors="Doe, J.; Roe, R.",
        category="neuroscience",
        published_at=date(2026, 11, 1),
        source="biorxiv",
        url=f"https://www.biorxiv.org/content/{doi}v1",
    )


def test_vector_extension_installed(db_engine: Engine) -> None:
    with db_engine.connect() as conn:
        rows = conn.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).all()
    assert len(rows) == 1


def test_papers_columns(db_engine: Engine) -> None:
    columns = {c["name"] for c in inspect(db_engine).get_columns("papers")}
    assert columns == {
        "id",
        "doi",
        "version",
        "title",
        "abstract",
        "authors",
        "category",
        "published_at",
        "source",
        "url",
        "created_at",
    }


def test_duplicate_doi_rejected(db_session: Session) -> None:
    db_session.add(_paper("10.1101/2026.11.01.000001"))
    db_session.commit()
    db_session.add(_paper("10.1101/2026.11.01.000001"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_default_urls_use_compose_port() -> None:
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert ":5433/" in s.DATABASE_URL
    assert ":5433/" in s.TEST_DATABASE_URL
