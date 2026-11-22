import os

os.environ["KEITARO_FAKE"] = "true"  # до импорта app: тесты не ходят в настоящий Keitaro

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import deps
from app.db import Base, get_db
from app.keitaro.fake import FakeKeitaro
from app.main import app
from app.services import offers as offers_service

DEMO_CAMPAIGN = 1001  # кампания из FakeKeitaro: потоки 5001 (редирект), 5002 (3 оффера), 5003 (без офферов)


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    yield session
    session.close()


@pytest.fixture()
def keitaro() -> FakeKeitaro:
    offers_service.clear_cache()
    deps._fake = FakeKeitaro()
    return deps._fake


@pytest.fixture()
def client(db, keitaro):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()
