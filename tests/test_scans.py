"""Tests for Step 3: uploading a scan and seeing your saved history."""

FAKE_IMAGE = ("mole.jpg", b"\xff\xd8\xff\xe0fake-jpeg-bytes", "image/jpeg")


async def auth_header(client, email):
    """Register + log in a user and return their Authorization header."""
    await client.post("/auth/register", json={"email": email, "password": "supersecret123"})
    token = (
        await client.post("/auth/login", json={"email": email, "password": "supersecret123"})
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_upload_requires_login(client):
    res = await client.post("/scans", files={"file": FAKE_IMAGE})
    assert res.status_code == 401


async def test_upload_creates_and_saves_a_scan(client):
    headers = await auth_header(client, "a@example.com")
    res = await client.post("/scans", files={"file": FAKE_IMAGE}, headers=headers)
    assert res.status_code == 201
    body = res.json()
    assert body["filename"] == "mole.jpg"
    assert "predicted_label" in body
    assert "id" in body


async def test_non_image_upload_is_rejected(client):
    headers = await auth_header(client, "b@example.com")
    res = await client.post(
        "/scans",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        headers=headers,
    )
    assert res.status_code == 400


async def test_history_lists_only_my_scans_newest_first(client):
    headers = await auth_header(client, "c@example.com")
    await client.post("/scans", files={"file": FAKE_IMAGE}, headers=headers)
    await client.post("/scans", files={"file": FAKE_IMAGE}, headers=headers)

    res = await client.get("/scans", headers=headers)
    assert res.status_code == 200
    scans = res.json()
    assert len(scans) == 2
    assert scans[0]["id"] > scans[1]["id"]  # newest first


async def test_cannot_see_another_users_scan(client):
    owner = await auth_header(client, "owner@example.com")
    created = await client.post("/scans", files={"file": FAKE_IMAGE}, headers=owner)
    scan_id = created.json()["id"]

    intruder = await auth_header(client, "intruder@example.com")
    res = await client.get(f"/scans/{scan_id}", headers=intruder)
    assert res.status_code == 404  # not yours = not found
