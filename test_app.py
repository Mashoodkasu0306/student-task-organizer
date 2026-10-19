import pytest
import app as organizer


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(organizer, "DB_PATH", str(tmp_path / "test.db"))
    return organizer.app.test_client()


def add(client, title, subject="Maths", due="2020-01-01", priority="High"):
    client.post("/add_task", data={"title": title, "subject": subject,
                                   "due_date": due, "priority": priority})


def test_calculate_percentage():
    assert organizer.calculate_percentage(1, 4) == 25.0
    assert organizer.calculate_percentage(0, 0) == 0.0


def test_get_status():
    assert organizer.get_status(0, 0, 0) == "No tasks yet"
    assert organizer.get_status(3, 3, 0) == "All done"
    assert organizer.get_status(1, 3, 1) == "Overdue"
    assert organizer.get_status(1, 3, 0) == "In progress"


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Student Task Organizer" in response.data


def test_add_task(client):
    add(client, "Write lab report")
    assert b"Write lab report" in client.get("/").data


def test_toggle_and_progress(client):
    add(client, "Task A")
    add(client, "Task B")
    client.post("/toggle/1")
    summary = organizer.get_summary()
    assert summary[0]["total"] == 2
    assert summary[0]["done"] == 1
    assert summary[0]["percentage"] == 50.0
    assert summary[0]["status"] == "Overdue"   # Task B is past its due date


def test_delete_task(client):
    add(client, "Temporary task")
    client.post("/delete/1")
    assert b"Temporary task" not in client.get("/").data
