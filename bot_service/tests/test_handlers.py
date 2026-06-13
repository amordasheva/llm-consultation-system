from types import SimpleNamespace
from unittest.mock import AsyncMock

from jose import jwt

from app.bot.handlers import cmd_token, handle_text
from app.core.config import settings


def _make_message(text, user_id=42, chat_id=42):
    return SimpleNamespace(
        text=text,
        from_user=SimpleNamespace(id=user_id),
        chat=SimpleNamespace(id=chat_id),
        answer=AsyncMock(),
    )


def _valid_token():
    return jwt.encode(
        {"sub": "1", "role": "user"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALG,
    )


async def test_token_command_saves_token(fake_redis):
    token = _valid_token()
    message = _make_message(text=f"/token {token}")
    command = SimpleNamespace(args=token)

    await cmd_token(message, command)

    saved = await fake_redis.get("token:42")
    assert saved == token
    message.answer.assert_awaited()


async def test_text_without_token_does_not_call_celery(fake_redis, mocker):
    delay = mocker.patch("app.bot.handlers.llm_request.delay")
    message = _make_message(text="Привет")

    await handle_text(message)

    delay.assert_not_called()
    message.answer.assert_awaited()


async def test_text_with_token_calls_celery(fake_redis, mocker):
    await fake_redis.set("token:42", _valid_token())
    delay = mocker.patch("app.bot.handlers.llm_request.delay")
    message = _make_message(text="Сколько будет 2+2?")

    await handle_text(message)

    delay.assert_called_once_with(42, "Сколько будет 2+2?")
    message.answer.assert_awaited()