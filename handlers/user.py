from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from utils.config import ADMIN_ID

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Привет, Админ! Я готов присылать посты на модерацию.")
    else:
        await message.answer("Привет! Я приватный IT бот-агрегатор.")
