from ..db import DB
from typing import Union, List
from dataclasses import dataclass

@dataclass
class User:
    ADMIN = "admin"
    USER = "user"

    id:int
    role:str
    access:bool
    phrases_limit:int

class UserStorage():
    __table = "users"
    def __init__(self, db:DB):
        self._db = db
    
    async def init(self):
        await self._db.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.__table} (
                id BIGINT PRIMARY KEY,
                role TEXT,
                access BOOLEAN,
                phrases_limit BIGINT
            )
        ''')

    async def get_by_id(self, id:int) -> User | None:
        data = await self._db.fetchrow(f"SELECT * FROM {self.__table} WHERE id = $1", id)
        if data is None:
            return None
        return User(data[0], data[1], data[2], data[3])

    async def get_admins(self) -> List[User] | None:
        admins = await self._db.fetch(f"SELECT * FROM {self.__table} WHERE role = $1", User.ADMIN)
        if admins is None:
            return None
        return [User(admin[0], admin[1], admin[2], admin[3]) for admin in admins]

    async def create(self, user:User):
        await self._db.execute(f'''
            INSERT INTO {self.__table} (id, role, access, phrases_limit) VALUES ($1, $2, $3, $4)
        ''', user.id, user.role, user.access, user.phrases_limit)

    async def decrease_phrase_limit(self, user:User):
        await self._db.execute(f"UPDATE {self.__table} SET phrases_limit = phrases_limit - 1 WHERE id = $1", user.id)

    async def delete(self, user_id:int):
        await self._db.execute(f'''
            DELETE FROM {self.__table} WHERE id = $1
        ''', user_id)