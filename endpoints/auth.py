from core.errors import AUTH_EXC
from endpoints.depends import get_session, get_user_repository
from models.token import Token, Login
from fastapi import APIRouter, Depends
from repositories.users import UserRepository
from core.security import verify_password, create_access_token
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/", response_model=Token)
async def login(
    login: Login,
    users: UserRepository = Depends(get_user_repository),
    session: AsyncSession = Depends(get_session)):
    user = await users.get_user_by_email(session, login.email)
    if user is None or not verify_password(login.password, user.hash_password):
        raise AUTH_EXC
    return Token(
        access_token=create_access_token({"sub": user.email}),
        token_type="Bearer"
    )