from collections.abc import Iterator

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import settings


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    engine = create_engine(
        settings.TEST_DATABASE_URL, connect_args={"connect_timeout": 3}
    )
    try:
        with engine.connect():
            pass
    except OperationalError:
        pytest.fail(
            "Test database unreachable — run `docker compose up -d` "
            "from the repo root"
        )
    cfg = Config("alembic.ini")
    cfg.attributes["url"] = settings.TEST_DATABASE_URL
    command.upgrade(cfg, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    with db_engine.begin() as conn:
        conn.execute(text("TRUNCATE papers RESTART IDENTITY"))
    with Session(db_engine) as session:
        yield session
