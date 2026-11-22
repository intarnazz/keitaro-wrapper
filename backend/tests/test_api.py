from tests.conftest import DEMO_CAMPAIGN


def ok(r, status=200):
    assert r.status_code == status, r.text
    body = r.json()
    assert body["success"] is True and body["message"] == "success"
    return body["data"]


def test_editor_flow_over_http(client):
    campaigns = ok(client.get("/api/campaigns"))
    assert campaigns[0]["id"] == DEMO_CAMPAIGN and campaigns[0]["name"] == "Demo AU"
    assert ok(client.get(f"/api/campaigns/{DEMO_CAMPAIGN}"))["alias"] == "demo-au"

    assert ok(client.get(f"/api/campaigns/{DEMO_CAMPAIGN}/streams")) == []  # до Fetch локально пусто
    streams = ok(client.post(f"/api/campaigns/{DEMO_CAMPAIGN}/fetch"))
    assert [s["is_editable"] for s in streams] == [False, True, False]
    sid = streams[1]["id"]

    found = ok(client.get("/api/offers", params={"q": "dating"}))
    assert [o["id"] for o in found] == [3]
    assert [o["id"] for o in ok(client.get("/api/offers", params={"q": "7"}))] == [7]

    s = ok(client.post(f"/api/streams/{sid}/offers", json={"offer_id": 4}))
    assert s["dirty"] and [o["share"] for o in s["offers"]] == [25, 25, 25, 25] and s["total_share"] == 100
    s = ok(client.put(f"/api/streams/{sid}/offers/1/pin", json={"pinned": True}))
    assert s["offers"][0]["pinned"] is True
    s = ok(client.post(f"/api/streams/{sid}/offers/2/remove"))
    assert s["offers"][-1]["status"] == "removed" and s["offers"][-1]["share"] == 0
    s = ok(client.post(f"/api/streams/{sid}/push"))
    assert not s["dirty"] and s["total_share"] == 100
    s = ok(client.post(f"/api/streams/{sid}/offers/2/restore"))
    s = ok(client.post(f"/api/streams/{sid}/cancel"))
    assert not s["dirty"]


def test_errors_use_envelope(client):
    r = client.post("/api/streams/999/push")
    assert r.status_code == 404
    assert r.json()["success"] is False and "Fetch" in r.json()["message"]

    r = client.get("/api/campaigns/424242")
    assert r.status_code == 404 and r.json()["success"] is False

    ok(client.post(f"/api/campaigns/{DEMO_CAMPAIGN}/fetch"))
    r = client.put("/api/streams/2/offers/1/pin", json={"pinned": True, "share": 500})
    assert r.status_code == 422 and r.json()["data"]["required_fields"] == ["pinned"]

    r = client.post("/api/streams/2/offers", json={"offer_id": 99999})
    assert r.status_code == 404 and r.json()["message"].startswith("Keitaro:")


def test_create_campaign_over_http_with_fake_keitaro(client, keitaro):
    data = ok(client.post("/api/campaigns", json={"name": "My AU", "geo": "au", "offer_id": 5}), 201)
    assert data["domain_id"] == 1 and len(data["streams"]) == 2
    streams = keitaro.campaign_streams(data["campaign_id"])
    assert streams[0]["filters"][0]["payload"] == ["AU"] and streams[1]["offers"][0]["offer_id"] == 5

    r = client.post("/api/campaigns", json={"name": "My AU", "geo": "au", "offer_id": 5})
    assert r.status_code == 422 and r.json()["message"] == "Keitaro: name: Name has already been used"

    r = client.post("/api/campaigns", json={"name": "Broken", "geo": "au", "offer_id": 99999})
    assert r.status_code == 422 and r.json()["success"] is False
    # откат: имя освобождено, повтор с тем же именем проходит
    ok(client.post("/api/campaigns", json={"name": "Broken", "geo": "au", "offer_id": 5}), 201)
