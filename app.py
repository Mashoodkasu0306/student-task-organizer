import os
import sqlite3
from datetime import date
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "data/tasks.db")
PRIORITIES = ("High", "Medium", "Low")


def get_db():
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tasks ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, "
        "subject TEXT NOT NULL, due_date TEXT NOT NULL, "
        "priority TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)"
    )
    return conn


def calculate_percentage(done, total):
    if total == 0:
        return 0.0
    return round(done * 100 / total, 1)


def get_status(done, total, overdue):
    if total == 0:
        return "No tasks yet"
    if done == total:
        return "All done"
    if overdue > 0:
        return "Overdue"
    return "In progress"


def get_tasks():
    today = date.today().isoformat()
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tasks ORDER BY done, due_date, id"
    ).fetchall()
    conn.close()
    return [
        {**dict(r), "overdue": (not r["done"]) and r["due_date"] < today}
        for r in rows
    ]


def get_summary():
    today = date.today().isoformat()
    conn = get_db()
    rows = conn.execute(
        """
        SELECT subject, COUNT(*) AS total, SUM(done) AS done,
               SUM(CASE WHEN done = 0 AND due_date < ? THEN 1 ELSE 0 END) AS overdue
        FROM tasks GROUP BY subject ORDER BY subject
        """,
        (today,),
    ).fetchall()
    conn.close()
    return [
        {
            "subject": r["subject"],
            "total": r["total"],
            "done": r["done"],
            "percentage": calculate_percentage(r["done"], r["total"]),
            "status": get_status(r["done"], r["total"], r["overdue"]),
        }
        for r in rows
    ]


PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Student Task Organizer</title>
<style>
body { font-family: Arial, sans-serif; max-width: 860px; margin: 30px auto; padding: 0 15px; }
table { border-collapse: collapse; width: 100%; margin-top: 10px; }
th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
th { background: #f0f0f0; }
.box { border: 1px solid #ddd; padding: 12px; margin-top: 15px; border-radius: 6px; }
.good { color: green; font-weight: bold; }
.bad { color: red; font-weight: bold; }
.mid { color: #b36b00; font-weight: bold; }
.done-task { text-decoration: line-through; color: #888; }
</style>
</head>
<body>
<h2>Student Task Organizer</h2>
<p>DevOps Pipeline Successfully Executed</p>

<div class="box">
<h3>1. Add a Task</h3>
<form method="post" action="/add_task">
<input name="title" placeholder="e.g. Finish DevOps lab report" required>
<input name="subject" placeholder="Subject e.g. ASD" required>
<input type="date" name="due_date" value="{{ today }}" required>
<select name="priority">
{% for p in priorities %}<option>{{ p }}</option>{% endfor %}
</select>
<button type="submit">Add Task</button>
</form>
</div>

<h3>2. My Tasks</h3>
<table>
<tr><th>Task</th><th>Subject</th><th>Due</th><th>Priority</th><th>Action</th></tr>
{% for t in tasks %}
<tr>
<td class="{{ 'done-task' if t.done }}">{{ t.title }}</td>
<td>{{ t.subject }}</td>
<td>{{ t.due_date }}{% if t.overdue %} <span class="bad">(overdue)</span>{% endif %}</td>
<td>{{ t.priority }}</td>
<td>
<form method="post" action="/toggle/{{ t.id }}" style="display:inline">
<button type="submit">{{ 'Undo' if t.done else 'Done' }}</button></form>
<form method="post" action="/delete/{{ t.id }}" style="display:inline">
<button type="submit">Delete</button></form>
</td>
</tr>
{% else %}
<tr><td colspan="5">No tasks yet. Add one above.</td></tr>
{% endfor %}
</table>

<h3>3. Progress by Subject</h3>
<table>
<tr><th>Subject</th><th>Completed</th><th>Total Tasks</th><th>Progress</th><th>Status</th></tr>
{% for s in summary %}
<tr>
<td>{{ s.subject }}</td><td>{{ s.done }}</td><td>{{ s.total }}</td><td>{{ s.percentage }}%</td>
<td class="{{ 'good' if s.status == 'All done' else 'bad' if s.status == 'Overdue' else 'mid' }}">{{ s.status }}</td>
</tr>
{% endfor %}
</table>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(
        PAGE,
        tasks=get_tasks(),
        summary=get_summary(),
        today=date.today().isoformat(),
        priorities=PRIORITIES,
    )


@app.route("/add_task", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    subject = request.form.get("subject", "").strip()
    due_date = request.form.get("due_date", "")
    priority = request.form.get("priority", "")
    try:
        date.fromisoformat(due_date)
    except ValueError:
        return redirect("/")
    if title and subject and priority in PRIORITIES:
        conn = get_db()
        conn.execute(
            "INSERT INTO tasks (title, subject, due_date, priority) VALUES (?, ?, ?, ?)",
            (title, subject, due_date, priority),
        )
        conn.commit()
        conn.close()
    return redirect("/")


@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle(task_id):
    conn = get_db()
    conn.execute("UPDATE tasks SET done = 1 - done WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
