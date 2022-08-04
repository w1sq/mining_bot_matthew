from ..db import DB
from typing import Union, List
from dataclasses import dataclass

@dataclass
class User:
    ADMIN = "admin"
    USER = "user"
    BLOCKED = "blocked"
    PAID = "paid"

    id:int
    role:str
    actual_limit:int
    daily_limit:int

class UserStorage():
    __table = "users"
    def __init__(self, db:DB):
        self._db = db
    
    async def init(self):
        await self._db.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.__table} (
                id BIGINT PRIMARY KEY,
                role TEXT,
                actual_limit BIGINT,
                daily_limit BIGINT
            )
        ''')

    async def get_by_id(self, id:int) -> User | None:
        data = await self._db.fetchrow(f"SELECT * FROM {self.__table} WHERE id = $1", id)
        if data is None:
            return None
        return User(data[0], data[1], data[2], data[3])

    async def promote_to_admin(self, id:int):
        await self._db.execute(f"UPDATE {self.__table} SET role = $1 WHERE id = $2", User.ADMIN, id)

    async def demote_from_admin(self, id:int):
        await self._db.execute(f"UPDATE {self.__table} SET role = $1 WHERE id = $2", User.USER, id)

    async def get_role_list(self, role:str) -> List[int] | None:
        roles = await self._db.fetch(f"SELECT * FROM {self.__table} WHERE role = $1", role)
        if roles is None:
            return None
        return [role[0] for role in roles]

    async def create(self, user:User):
        await self._db.execute(f'''
            INSERT INTO {self.__table} (id, role, actual_limit, daily_limit) VALUES ($1, $2, $3, $4)
        ''', user.id, user.role, user.actual_limit, user.daily_limit)

    async def reset_limit(self, user:User):
        await self._db.execute(f"UPDATE {self.__table} SET actual_limit = daily_limit WHERE id = $1", user.id)

    async def get_all_members(self) -> List[User]| None:
        data = await self._db.fetch(f'''
            SELECT * FROM {self.__table}
        ''')
        if data is None:
            return None
        return [User(user_data[0], user_data[1], user_data[2], user_data[3]) for user_data in data]

    async def give_referal(self, inviter_id:int):
        await self._db.execute(f'''
            UPDATE {self.__table} SET actual_limit = actual_limit + 30 WHERE id = $1
        ''', inviter_id)

    async def get_user_amount(self) -> int:
        return await self._db.fetchval(f"SELECT COUNT(*) FROM {self.__table}")

    async def change_phrase_limit(self, user:User, delta:int):
        await self._db.execute(f"UPDATE {self.__table} SET daily_limit = daily_limit + $1 WHERE id = $2", delta, user.id)

    async def decrease_phrases(self, user:User):
        await self._db.execute(f"UPDATE {self.__table} SET actual_limit = actual_limit - 1 WHERE id = $1", user.id)

    async def add_paid(self, user:User):
        await self._db.execute(f"UPDATE {self.__table} SET role = $1 WHERE id = $2", User.PAID, user.id)
    
    async def remove_paid(self, user:User):
        await self._db.execute(f"UPDATE {self.__table} SET role = $1 WHERE id = $2", User.USER, user.id)

    async def add_admin(self, user:User):
        await self._db.execute(f"UPDATE {self.__table} SET role = $1 WHERE id = $2", User.ADMIN, user.id)

    async def delete(self, user_id:int):
        await self._db.execute(f'''
            DELETE FROM {self.__table} WHERE id = $1
        ''', user_id)