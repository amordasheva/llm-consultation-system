import httpx
import respx

from app.core.config import settings
from app.services.openrouter_client import call_openrouter


@respx.mock
def test_call_openrouter_returns_text():
    route = respx.post(f"{settings.OPENROUTER_BASE_URL}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": "42"}}]},
        )
    )

    result = call_openrouter("What is the answer?")

    assert result == "42"
    assert route.called