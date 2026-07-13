import html
import logging
from aiogram import Router, F
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from database.models import PostStatus
import database.requests as db_req
from utils.config import CHANNEL_ID, ADMIN_ID

router = Router()


class ModerationCallback(CallbackData, prefix="mod"):
    action: str
    post_id: int


@router.callback_query(ModerationCallback.filter(F.action == "approve"))
async def approve_handler(callback: CallbackQuery, callback_data: ModerationCallback):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "У вас нет прав для управления этим ботом! 🛑", show_alert=True
        )
        return

    post = await db_req.get_post_by_id(callback_data.post_id)

    # ТЕПЕРЬ ПРОВЕРЯЕМ СТАТУС SENT_TO_ADMIN
    if not post or post.status != PostStatus.SENT_TO_ADMIN:
        await callback.answer("Пост уже обработан или не найден.", show_alert=True)
        return

    safe_title = html.escape(post.title)
    safe_summary = html.escape(post.summary)
    safe_hub = html.escape(post.hub_name)

    channel_text = (
        f"🔥 <b>{safe_title}</b>\n\n"
        f"{safe_summary}\n\n"
        f"🔗 <a href='{post.source_url}'>Читать полную статью</a>\n\n"
        f"#{safe_hub.lower()}"
    )

    try:
        await callback.bot.send_message(
            chat_id=CHANNEL_ID, text=channel_text, parse_mode="HTML"
        )
        await db_req.update_post_status(post.id, PostStatus.PUBLISHED)

        updated_admin_text = (
            f"🏷 <b>Тема: #{safe_hub}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Заголовок:</b> {safe_title}\n\n"
            f"<b>Превью:</b> {safe_summary}\n\n"
            f"🔗 <a href='{post.source_url}'>Открыть оригинал статьи</a>\n\n"
            f"📢 <b>Статус:</b> Опубликовано в канал ✅"
        )

        await callback.message.edit_text(
            text=updated_admin_text, parse_mode="HTML", reply_markup=None
        )
        await callback.answer("Успешно опубликовано!")
    except Exception as e:
        logging.error(f"Ошибка при публикации в канал: {e}")
        await callback.answer("Ошибка при отправке в канал!", show_alert=True)


@router.callback_query(ModerationCallback.filter(F.action == "reject"))
async def reject_handler(callback: CallbackQuery, callback_data: ModerationCallback):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "У вас нет прав для управления этим ботом! 🛑", show_alert=True
        )
        return

    post = await db_req.get_post_by_id(callback_data.post_id)

    # ТЕПЕРЬ ПРОВЕРЯЕМ СТАТУС SENT_TO_ADMIN
    if not post or post.status != PostStatus.SENT_TO_ADMIN:
        await callback.answer("Пост уже обработан.", show_alert=True)
        return

    await db_req.update_post_status(post.id, PostStatus.REJECTED)

    safe_title = html.escape(post.title)
    safe_summary = html.escape(post.summary)
    safe_hub = html.escape(post.hub_name)

    updated_admin_text = (
        f"🏷 <b>Тема: #{safe_hub}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Заголовок:</b> {safe_title}\n\n"
        f"<b>Превью:</b> {safe_summary}\n\n"
        f"🔗 <a href='{post.source_url}'>Открыть оригинал статьи</a>\n\n"
        f"📢 <b>Статус:</b> Отклонено админом ❌"
    )

    await callback.message.edit_text(
        text=updated_admin_text, parse_mode="HTML", reply_markup=None
    )
    await callback.answer("Отклонено.")
