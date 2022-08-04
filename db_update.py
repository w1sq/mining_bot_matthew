import asyncio
from db.db import DB
from config import Config

async def init_db():
    db = DB(host=Config.host, port=Config.port, login=Config.login, password=Config.password, database = Config.database)
    await db.init()
    return db

async def main():
    db = await init_db()
    await db.execute(f'ALTER TABLE users ADD COLUMN "present" BOOLEAN NOT NULL DEFAULT FALSE;;')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())