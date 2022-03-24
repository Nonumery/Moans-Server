from unittest import mock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from repositories.users import UserRepository
from models.users import User, UserIn

pytestmark = pytest.mark.asyncio


async def test_coupon_create(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    user_repository = UserRepository()
    payload = {
        "email": "test_email@test.com",
        "password": 'stringst',
        "password2": 'stringst'
    }

    response = await async_client.post("/users/", json=payload)
    user = await user_repository.get_user_by_id(db_session, int(response.json()["id"]))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['id'] == str(user.id)
    assert response.json()['email'] == payload['email']

"""
async def test_coupon_get_by_id(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    payload = {
        "email": "test2_email@test.com",
        "password": 'stringst',
    }
    user_repository = UserRepository(db_session)
    coupon = await user_repository.add_user(db_session, UserIn(**payload))
    response = await async_client.get(f"/track/{coupon.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "code": payload["code"],
        "init_count": payload["init_count"],
        "remaining_count": payload["init_count"],
        "id": mock.ANY,
    }
    """