from fastapi import Depends
from core.errors import CRED_EXC
from core.security import JWTBearer, decode_access_token
from models.users import User
from repositories.tracks import TrackRepository
from repositories.users import UserRepository
from db.tables import async_session
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
        await session.commit()

def get_user_repository() -> UserRepository:
    return UserRepository()



async def get_current_user(
    users: UserRepository = Depends(get_user_repository),
    session : AsyncSession = Depends(get_session),
    token: str = Depends(JWTBearer())
    ) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise CRED_EXC
    email: str = payload.get("sub")
    if email is None:
        raise CRED_EXC
    user = await users.get_user_by_email(session, email)
    if user is None:
        raise CRED_EXC
    return user

def get_track_repository() -> TrackRepository:
    return TrackRepository()


    