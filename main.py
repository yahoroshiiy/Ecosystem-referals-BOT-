import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apps.hand import router
from apps.database.models import async_main

async def main():
    print("Инициализация базы данных...")
    await async_main()
    
    bot = Bot(token='8127628251:AAG9yG3mE0c3Qd5id6vqQj8Lv7vZZZ2MJoo')
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(router)
    
    print("Бот запускается...")
    await dp.start_polling(bot)
    print("Бот остановлен.")

if __name__ == '__main__':
    asyncio.run(main())