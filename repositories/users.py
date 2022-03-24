import datetime
from typing import List, Optional
from models.users import User, UserIn
from db.tables import UserTable
from core.security import hash_password
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository():

    async def get_users(self, session: AsyncSession, limit: int = 10, skip: int = 0) -> List[User]:
        result = await session.execute(select(UserTable).limit(limit).offset(skip))
        return [User.parse_obj(user.__dict__) for user in result.scalars().all()]
    
    async def get_user_by_id(self, session: AsyncSession, id: int) -> Optional[User]:
        query = select(UserTable).where(UserTable.id==id)
        user = (await session.execute(query)).scalars().first()
        if user is None:
            return None
        return User.parse_obj({**user.__dict__})
    
    async def add_user(self, session: AsyncSession, email:str, password:str) -> User:
        user = UserTable(
            email = email,
            hash_password=hash_password(password)
        )
        session.add(user)
        result = await session.execute(select(UserTable).where(UserTable.email==user.email))
        user = result.scalars().first()
        #await session.commit()
        return User.parse_obj({**user.__dict__})
    
    async def update_user(self, session: AsyncSession, id: int, email : str, password : str) -> User:
        query = select(UserTable).filter_by(id=id)
        user = (await session.execute(query)).scalar_one()
        user.email = email
        user.hash_password = hash_password(password)
        return User.parse_obj({**user.__dict__})
    
    async def get_user_by_email(self, session : AsyncSession, email: str) -> Optional[User]:
        query = select(UserTable).where(UserTable.email==email)
        user = (await session.execute(query)).scalars().first()
        if user is None:
            return None
        return User.parse_obj({**user.__dict__})
    
    
    