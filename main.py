import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from handlers.user_handlers import router as user_router
from handlers.admin_handlers import router as admin_router
from config import BOT_TOKEN, ADMIN_TOKEN, DATABASE_NAME
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from database import Database
from utils.reminders import send_reminders
from aiohttp import web

db = Database(DATABASE_NAME)


# Создаём простой HTTP-эндпоинт для UptimeRobot
async def health_check(request):
    return web.Response(text="OK")


async def start_web_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)  # Render использует порт 8080
    await site.start()
    print("HTTP-сервер запущен на порту 8080")


async def main():
    # Инициализация ботов с DefaultBotProperties
    user_bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    admin_bot = Bot(token=ADMIN_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Создаем отдельные диспетчеры для каждого бота
    user_dp = Dispatcher()
    admin_dp = Dispatcher()

    # Регистрируем роутеры
    user_dp.include_router(user_router)
    admin_dp.include_router(admin_router)

    # Инициализируем планировщик для пользовательского бота
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_reminders,
        "interval",
        days=1,
        args=(user_bot,),
        next_run_time=datetime.now() + timedelta(seconds=10)
    )
    scheduler.start()

    # Запускаем веб-сервер для health check
    asyncio.create_task(start_web_server())

    print("Бот запущен!")

    # Создаем задачи для поллинга
    user_polling = user_dp.start_polling(user_bot)
    admin_polling = admin_dp.start_polling(admin_bot)

    # Запускаем обе задачи параллельно
    await asyncio.gather(user_polling, admin_polling)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот ВИМКНЕНО")