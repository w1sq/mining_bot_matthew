import asyncio
from db.db import DB
from db.storage import UserStorage, PhrasesStorage
from config import Config

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
    users = await user_storage.get_all_members()
    for user in users:
        await user_storage.reset_limit(user)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())