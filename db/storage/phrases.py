from ..db import DB
from typing import Union, List
from dataclasses import dataclass

@dataclass
class Phrase:
    id:int
    text:str

class PhrasesStorage():
    __table = "phrases"
    def __init__(self, db:DB):
        self._db = db
    
    async def init(self):
        await self._db.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.__table} (
                id SERIAL PRIMARY KEY,
                text TEXT
            )
        ''')

    async def get_by_id(self, id:int) -> Phrase | None:
        data = await self._db.fetchrow(f"SELECT * FROM {self.__table} WHERE id = $1", id)
        if data is None:
            return None
        return Phrase(data[0], data[1])

    async def get_random_phrase(self) -> str | None:
        data = await self._db.fetchrow(f"SELECT * FROM {self.__table} ORDER BY random() LIMIT 1")
        if data is None:
            return None
        # await self.delete(data[0])
        return data[1]

    async def create(self, phrase:str):
        await self._db.execute(f'''
            INSERT INTO {self.__table} (text) VALUES ($1)
        ''',phrase)

    async def get_phrases_amount(self) -> int:
        return await self._db.fetchval(f"SELECT COUNT(*) FROM {self.__table}")

    async def delete(self, phrase_id:int):
        await self._db.execute(f'''
            DELETE FROM {self.__table} WHERE id = $1
        ''', phrase_id)