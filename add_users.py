import asyncio
from db.db import DB
from db.storage import UserStorage, PhrasesStorage
from config import Config
from db.storage import User
import asyncpg

async def init_db():
    db = DB(host=Config.host, port=Config.port, login=Config.login, password=Config.password, database = Config.database)
    await db.init()
    user_storage = UserStorage(db)
    phrases_storage = PhrasesStorage(db)
    await phrases_storage.init()
    await user_storage.init()
    return user_storage, phrases_storage

async def main():
    user_storage, phrases_storage = await init_db()
    with open('users.txt','r') as f:
        users=f.readlines()
        i = 0
        for user in users:
            print(i)
            i += 1
            user = User(int(user), User.USER, 10, 10)
            try:
                await user_storage.create(user)
            except asyncpg.exceptions.UniqueViolationError:
                pass

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())