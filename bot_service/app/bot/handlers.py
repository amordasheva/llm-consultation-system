import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.core.jwt import InvalidTokenError, decode_and_validate
from app.infra.redis import get_redis
from app.tasks.llm_tasks import llm_request

logger = logging.getLogger(__name__)

router = Router()


def _token_key(user_id: int) -> str:
    return f"token:{user_id}"


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Сначала пришли JWT-токен командой /token <твой_токен>, "
        "потом задавай любой вопрос."
    )


@router.message(Command("token"))
async def cmd_token(message: Message, command: CommandObject) -> None:
    token = (command.args or "").strip()
    if not token:
        await message.answer("Использование: /token <jwt>")
        return

    redis = get_redis()
    await redis.set(_token_key(message.from_user.id), token)
    await message.answer("Токен принят и сохранён.")


@router.message()
async def handle_text(message: Message) -> None:
    redis = get_redis()
    token = await redis.get(_token_key(message.from_user.id))

    if not token:
        await message.answer(
            "Сначала авторизуйся: пришли токен командой /token <jwt>. "
            "Получить токен можно в Auth Service."
        )
        return

    try:
        decode_and_validate(token)
    except InvalidTokenError:
        await message.answer(
            "Токен истёк или невалиден. Пришли новый командой /token <jwt>."
        )
        return

    llm_request.delay(message.chat.id, message.text)
    await message.answer("Запрос принят, обрабатываю.")