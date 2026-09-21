def test_create_task(client, login):
    h = login()
    r = client.post("/api/v1/tasks", json={"title": "  Write tests  "}, headers=h)
    assert r.status_code == 201
    assert r.json()["title"] == "Write tests"
    assert r.json()["status"] == "todo"


def test_create_task_empty_title_rejected(client, login):
    r = client.post("/api/v1/tasks", json={"title": ""}, headers=login())
    assert r.status_code == 422


def test_list_returns_only_own_tasks(client, login):
    alice, bob = login("alice@example.com"), login("bob@example.com")
    client.post("/api/v1/tasks", json={"title": "alice task"}, headers=alice)
    client.post("/api/v1/tasks", json={"title": "bob task"}, headers=bob)
    r = client.get("/api/v1/tasks", headers=alice)
    assert [t["title"] for t in r.json()] == ["alice task"]


def test_filter_by_status(client, login):
    h = login()
    client.post("/api/v1/tasks", json={"title": "a", "status": "done"}, headers=h)
    client.post("/api/v1/tasks", json={"title": "b"}, headers=h)
    r = client.get("/api/v1/tasks?status=done", headers=h)
    assert [t["title"] for t in r.json()] == ["a"]


def test_pagination_limit_is_bounded(client, login):
    assert client.get("/api/v1/tasks?limit=1000", headers=login()).status_code == 422


def test_cannot_access_other_users_task(client, login):
    alice, bob = login("alice@example.com"), login("bob@example.com")
    task_id = client.post("/api/v1/tasks", json={"title": "secret"}, headers=alice).json()["id"]
    assert client.get(f"/api/v1/tasks/{task_id}", headers=bob).status_code == 404
    assert client.delete(f"/api/v1/tasks/{task_id}", headers=bob).status_code == 404


def test_update_task(client, login):
    h = login()
    task_id = client.post("/api/v1/tasks", json={"title": "x"}, headers=h).json()["id"]
    r = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"}, headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "done"
    assert r.json()["title"] == "x"


def test_update_null_title_rejected(client, login):
    h = login()
    task_id = client.post("/api/v1/tasks", json={"title": "x"}, headers=h).json()["id"]
    r = client.patch(f"/api/v1/tasks/{task_id}", json={"title": None}, headers=h)
    assert r.status_code == 422


def test_delete_task(client, login):
    h = login()
    task_id = client.post("/api/v1/tasks", json={"title": "x"}, headers=h).json()["id"]
    assert client.delete(f"/api/v1/tasks/{task_id}", headers=h).status_code == 204
    assert client.get(f"/api/v1/tasks/{task_id}", headers=h).status_code == 404
