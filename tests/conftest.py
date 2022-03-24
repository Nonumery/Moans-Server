import asyncio
import os
import shutil
from typing import AsyncGenerator, Generator, Callable

import pytest
from fastapi import FastAPI

from httpx import AsyncClient
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from db.tables import Base, LanguageTable, async_session, engine


@pytest.fixture(scope="session")
def event_loop(request) -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def db_session() -> AsyncSession:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        shutil.rmtree("tracks", ignore_errors=False, onerror=None)
        await conn.run_sync(Base.metadata.create_all)
        os.mkdir("tracks")
        await conn.execute(insert(LanguageTable).values(id = 0, language="rus"))
        await conn.execute(insert(LanguageTable).values(id = 1, language="eng"))
        async with async_session(bind=conn) as session:
            yield session
            await session.flush()
            await session.rollback()


@pytest.fixture()
def override_get_db(db_session: AsyncSession) -> Callable:
    async def _override_get_db():
        yield db_session

    return _override_get_db


@pytest.fixture()
def app(override_get_db: Callable) -> FastAPI:
    from endpoints.depends import get_session
    from main import app

    app.dependency_overrides[get_session] = override_get_db
    return app


@pytest.fixture()
async def async_client(app: FastAPI) -> AsyncGenerator:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac