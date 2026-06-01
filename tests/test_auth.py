"""Tests for Step 2: sign up, log in, and the 'who am I' check."""

EMAIL = "lakshmi@example.com"
PASSWORD = "supersecret123"


async def register(client, email=EMAIL, password=PASSWORD):
    return await client.post("/auth/register", json={"email": email, "password": password})


async def login(client, email=EMAIL, password=PASSWORD):
    return await client.post("/auth/login", json={"email": email, "password": password})


async def test_register_creates_account(client):
    res = await register(client)
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == EMAIL
    assert "id" in body
    assert "password" not in body  # never leak the password


async def test_register_duplicate_email_is_rejected(client):
    await register(client)
    res = await register(client)
    assert res.status_code == 409


async def test_register_short_password_is_rejected(client):
    res = await register(client, password="short")
    assert res.status_code == 422  # validation error


async def test_login_succeeds_and_returns_token(client):
    await register(client)
    res = await login(client)
    assert res.status_code == 200
    assert res.json()["access_token"]


async def test_login_with_wrong_password_fails(client):
    await register(client)
    res = await login(client, password="wrongpassword")
    assert res.status_code == 401


async def test_me_requires_a_token(client):
    res = await client.get("/auth/me")
    assert res.status_code == 401


async def test_me_returns_logged_in_user(client):
    await register(client)
    token = (await login(client)).json()["access_token"]
    res = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == EMAIL
