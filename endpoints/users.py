import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from core.security import verify_password
from db.tables import UserTable
from repositories.users import UserRepository
from .depends import get_current_user, get_session, get_user_repository
from models.users import User, UserChange, UserIn
from sqlalchemy.ext.asyncio import AsyncSession
router = APIRouter()  
    
@router.get("/", response_model=List[User], response_model_exclude=["hash_password"])
async def read_users(
    users: UserRepository = Depends(get_user_repository),
    session : AsyncSession = Depends(get_session),
    limit: int = 10, 
    skip: int = 0):
    return await users.get_users(session=session, limit=limit, skip=skip)

@router.post("/", response_model=User, response_model_exclude=["hash_password"])
async def create_user(
    user: UserIn,
    users: UserRepository = Depends(get_user_repository),
    session : AsyncSession = Depends(get_session)):
    c_user = await users.get_user_by_email(session, user.email)
    if c_user:
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="Email is already used")
    new_user = await users.add_user(session=session, email=user.email, password=user.password)
    if new_user:
        user_folder = f"tracks/user_{new_user.id}"
        if not os.path.isdir(user_folder):
            os.mkdir(user_folder)
    return new_user

@router.patch("/", response_model=User, response_model_exclude=["hash_password"])
async def update_user(
    user: UserChange,
    users: UserRepository = Depends(get_user_repository),
    current_user: User = Depends(get_current_user),
    session : AsyncSession = Depends(get_session)):
    #c_user = await users.get_user_by_id(session=session, id=id)
    #if c_user is None or c_user.email != current_user.email:
        #raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not found")
    c_user = await users.get_user_by_email(session, current_user.email)
    if c_user is None or not verify_password(user.password, c_user.hash_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong password")
    c_user = await users.get_user_by_email(session, user.email)
    if c_user is not None and c_user.email != current_user.email:
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="Email is already used")

    return await users.update_user(session, int(current_user.id), user.email, user.new_password)