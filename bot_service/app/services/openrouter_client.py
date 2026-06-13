import httpx

from app.core.config import settings


class OpenRouterError(Exception):
    pass


def call_openrouter(prompt: str) -> str:
    url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.OPENROUTER_SITE_URL,
        "X-Title": settings.OPENROUTER_APP_NAME,
    }
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
    except httpx.HTTPError as exc:
        raise OpenRouterError(f"Network error: {exc}") from exc

    if response.status_code != 200:
        raise OpenRouterError(
            f"OpenRouter returned {response.status_code}: {response.text}"
        )

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise OpenRouterError(f"Unexpected response format: {data}") from exc