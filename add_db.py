import asyncio
from db.db import DB
from db.storage import UserStorage, PhrasesStorage, KeysStorage
from config import Config
from db.storage import Key
import asyncpg

async def init_db():
    db = DB(host=Config.host, port=Config.port, login=Config.login, password=Config.password, database = Config.database)
    await db.init()
    user_storage = UserStorage(db)
    phrases_storage = PhrasesStorage(db)
    keys_storage = KeysStorage(db)
    await phrases_storage.init()
    await user_storage.init()
    await keys_storage.init()
    return user_storage, phrases_storage, keys_storage

async def main():
    user_storage, phrases_storage, keys_storage = await init_db()
    with open('db.txt','r') as f:
        dbs=f.readlines()
        i = 0
        for db in dbs:
            print(i)
            i += 1
            db_db = Key(text=db)
            try:
                await keys_storage.create(db_db)
            except asyncpg.exceptions.UniqueViolationError:
                pass

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())