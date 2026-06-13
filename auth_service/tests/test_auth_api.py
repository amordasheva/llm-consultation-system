async def test_full_auth_flow(client):
    resp = await client.post(
        "/auth/register",
        json={"email": "ivanova@email.com", "password": "secret123"},
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "ivanova@email.com"

    resp = await client.post(
        "/auth/login",
        data={"username": "ivanova@email.com", "password": "secret123"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "ivanova@email.com"


async def test_duplicate_registration_returns_409(client):
    payload = {"email": "dup@email.com", "password": "secret123"}
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/auth/register", json=payload)
    assert second.status_code == 409


async def test_login_with_wrong_password_returns_401(client):
    await client.post(
        "/auth/register",
        json={"email": "wrong@email.com", "password": "right-pass"},
    )
    resp = await client.post(
        "/auth/login",
        data={"username": "wrong@email.com", "password": "bad-pass"},
    )
    assert resp.status_code == 401


async def test_me_without_token_returns_401(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401