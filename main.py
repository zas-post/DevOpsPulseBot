import asyncio
import logging
import html
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from utils.config import BOT_TOKEN, ADMIN_ID
from database.models import Base, PostStatus
from database.connection import engine
import database.requests as db_req
from utils.parser import fetch_rss_posts
import handlers.user as user_handlers
import handlers.admin as admin_handlers


# 1. КОНТУР ПРОДЮСЕРА: Только скачивает и сохраняет в БД (раз в 15 минут)
async def check_and_aggregate_job():
    logging.info("Продюсер: Запуск проверки RSS лент...")
    raw_posts = await fetch_rss_posts()
    saved_count = 0

    for raw_post in raw_posts:
        if await db_req.is_post_exists(raw_post["source_url"]):
            continue

        await db_req.add_new_post(
            title=raw_post["title"],
            source_url=raw_post["source_url"],
            summary=raw_post["summary"],
            hub_name=raw_post["hub_name"],
        )
        saved_count += 1

    if saved_count > 0:
        logging.info(
            f"Продюсер: Успешно сохранено новых постов в очередь: {saved_count}"
        )


# 2. КОНТУР КОНСЬЮМЕРА: Достает по 1 посту из БД и плавно шлет админу (раз в 3 секунды)
async def queue_consumer_worker(bot: Bot):
    while True:
        try:
            new_post = await db_req.get_next_pending_post()

            if not new_post:
                await asyncio.sleep(1)
                continue

            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👍 Опубликовать",
                            callback_data=admin_handlers.ModerationCallback(
                                action="approve", post_id=new_post.id
                            ).pack(),
                        ),
                        InlineKeyboardButton(
                            text="👎 Отклонить",
                            callback_data=admin_handlers.ModerationCallback(
                                action="reject", post_id=new_post.id
                            ).pack(),
                        ),
                    ]
                ]
            )

            url_lower = new_post.source_url.lower()
            if "habr.com" in url_lower:
                source_name = "Хабре"
            elif "vc.ru" in url_lower:
                source_name = "VC"
            elif "tproger.ru" in url_lower:
                source_name = "Tproger"
            elif "dzone.com" in url_lower:
                source_name = "DZone"
            elif "dev.to" in url_lower:
                source_name = "Dev.to"
            else:
                source_name = "оригинальном сайте"

            safe_title = html.escape(new_post.title)
            safe_summary = html.escape(new_post.summary)
            safe_hub = html.escape(new_post.hub_name)

            text = (
                f"🏷 <b>Тема: #{safe_hub}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📥 <b>Новый пост на модерацию!</b>\n\n"
                f"<b>Заголовок:</b> {safe_title}\n\n"
                f"<b>Превью:</b> {safe_summary}\n\n"
                f"🔗 <a href='{new_post.source_url}'>Посмотреть полную статью на {source_name}</a>"
            )

            await bot.send_message(
                chat_id=ADMIN_ID, text=text, reply_markup=markup, parse_mode="HTML"
            )
            await db_req.update_post_status(new_post.id, PostStatus.SENT_TO_ADMIN)
            logging.info(
                f"Консьюмер: Отправлена карточка модерации для поста ID {new_post.id}"
            )

            await asyncio.sleep(3.0)

        except Exception as e:
            logging.error(f"Ошибка в воркере очереди консьюмера: {e}")
            await asyncio.sleep(5)


async def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_and_aggregate_job, trigger=IntervalTrigger(minutes=15))
    scheduler.start()

    asyncio.create_task(check_and_aggregate_job())
    asyncio.create_task(queue_consumer_worker(bot))

    logging.info("Бот успешно запущен в режиме архитектуры очередей!")
    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
