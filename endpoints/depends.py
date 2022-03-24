from fastapi import Depends, HTTPException, status
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
    cred_exception = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Credentials are not valid")
    payload = decode_access_token(token)
    if payload is None:
        raise cred_exception
    email: str = payload.get("sub")
    if email is None:
        raise cred_exception
    user = await users.get_user_by_email(session, email)
    if user is None:
        raise cred_exception
    return user

def get_track_repository() -> TrackRepository:
    return TrackRepository()


    