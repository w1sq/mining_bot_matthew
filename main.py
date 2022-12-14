import asyncio
from db.db import DB
from bot import TG_Bot
from db.storage import UserStorage, PhrasesStorage, KeysStorage
from config import Config
import aioschedule as schedule

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

async def check_schedule():
    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)

async def main():
    user_storage, phrases_storage, keys_storage = await init_db()
    tg_bot = TG_Bot(user_storage, phrases_storage, keys_storage)
    await tg_bot.init()
    await tg_bot.start()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(check_schedule())
    loop.run_until_complete(main())