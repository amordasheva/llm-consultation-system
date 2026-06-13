import httpx

from app.core.config import settings
from app.infra.celery_app import celery_app
from app.services.openrouter_client import call_openrouter


def _send_telegram_message(chat_id: int, text: str) -> None:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    httpx.post(url, json={"chat_id": chat_id, "text": text}, timeout=30.0)


@celery_app.task(name="llm_request")
def llm_request(tg_chat_id: int, prompt: str) -> str:
    try:
        answer = call_openrouter(prompt)
    except Exception as exc:  # noqa: BLE001
        answer = f"Произошла ошибка при обращении к LLM: {exc}"

    _send_telegram_message(tg_chat_id, answer)
    return answer