import os
import sqlite3
from datetime import date
from email.utils import parseaddr
from pathlib import Path
from urllib.parse import urlencode

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "workhub.db"

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "change-this-in-production"),
    DATABASE=str(DATABASE),
)

CATEGORIES = [
    "Laporan Monitoring Perusahaan", "Laporan Monitoring Divisi",
    "Laporan Monitoring Cabang", "Laporan Monitoring Unit",
    "Kajian Risiko", "AOI RMI", "Pekerjaan Lainnya",
]
STATUSES = ["Belum Dimulai", "Dalam Proses", "Menunggu Review", "Selesai"]
PRIORITIES = ["Rendah", "Sedang", "Tinggi", "Kritis"]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))
    db.commit()


@app.cli.command("init-db")
def init_db_command():
    init_db()
    print("Database Workhub berhasil dibuat.")


@app.context_processor
def inject_globals():
    return {"categories": CATEGORIES, "statuses": STATUSES, "priorities": PRIORITIES}


@app.get("/")
def index():
    db = get_db()
    query = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    category = request.args.get("category", "")
    sql = "SELECT * FROM work_items WHERE 1=1"
    params = []
    if query:
        sql += " AND (title LIKE ? OR pic LIKE ? OR assignees LIKE ? OR category LIKE ?)"
        needle = f"%{query}%"
        params.extend([needle] * 4)
    if status in STATUSES:
        sql += " AND status = ?"
        params.append(status)
    if category in CATEGORIES:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY CASE WHEN deadline = '' THEN 1 ELSE 0 END, deadline, id DESC"
    items = [dict(row) for row in db.execute(sql, params).fetchall()]
    all_items = [dict(row) for row in db.execute("SELECT * FROM work_items").fetchall()]
    today = date.today().isoformat()
    for item in items:
        item["overdue"] = item["status"] != "Selesai" and item["deadline"] and item["deadline"] < today
    metrics = {
        "active": sum(i["status"] != "Selesai" for i in all_items),
        "overdue": sum(i["status"] != "Selesai" and bool(i["deadline"]) and i["deadline"] < today for i in all_items),
        "review": sum(i["status"] == "Menunggu Review" for i in all_items),
        "done": sum(i["status"] == "Selesai" for i in all_items),
        "studies": sum(i["category"] == "Kajian Risiko" for i in all_items),
    }
    status_counts = {s: sum(i["status"] == s for i in all_items) for s in STATUSES}
    return render_template("index.html", items=items, metrics=metrics,
                           status_counts=status_counts, total=len(all_items),
                           query=query, selected_status=status,
                           selected_category=category)


@app.post("/items")
def create_item():
    title = request.form.get("title", "").strip()
    if not title:
        flash("Judul pekerjaan wajib diisi.", "error")
        return redirect(url_for("index"))
    category = request.form.get("category", "Pekerjaan Lainnya")
    priority = request.form.get("priority", "Sedang")
    if category not in CATEGORIES or priority not in PRIORITIES:
        flash("Kategori atau prioritas tidak valid.", "error")
        return redirect(url_for("index"))
    db = get_db()
    db.execute("""
        INSERT INTO work_items
        (title, category, pic, assignees, priority, status, progress,
         deadline, drive_url, notes)
        VALUES (?, ?, ?, ?, ?, 'Belum Dimulai', 0, ?, ?, ?)
    """, (title, category, request.form.get("pic", "").strip(),
          request.form.get("assignees", "").strip(), priority,
          request.form.get("deadline", ""), request.form.get("drive_url", "").strip(),
          request.form.get("notes", "").strip()))
    db.commit()
    flash("Pekerjaan berhasil ditambahkan.", "success")
    return redirect(url_for("index"))


@app.post("/items/<int:item_id>/update")
def update_item(item_id):
    status = request.form.get("status", "")
    try:
        progress = max(0, min(100, int(request.form.get("progress", 0))))
    except ValueError:
        progress = 0
    if status not in STATUSES:
        flash("Status tidak valid.", "error")
        return redirect(url_for("index"))
    if status == "Selesai":
        progress = 100
    db = get_db()
    db.execute("UPDATE work_items SET status=?, progress=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
               (status, progress, item_id))
    db.commit()
    flash("Progres berhasil diperbarui.", "success")
    return redirect(url_for("index"))


@app.post("/items/<int:item_id>/delete")
def delete_item(item_id):
    db = get_db()
    db.execute("DELETE FROM work_items WHERE id=?", (item_id,))
    db.commit()
    flash("Pekerjaan telah dihapus.", "success")
    return redirect(url_for("index"))


@app.get("/items/<int:item_id>/email")
def disposition_email(item_id):
    item = get_db().execute("SELECT * FROM work_items WHERE id=?", (item_id,)).fetchone()
    if item is None:
        flash("Pekerjaan tidak ditemukan.", "error")
        return redirect(url_for("index"))
    recipient = parseaddr(item["assignees"])[1]
    body = (f"Yth. {item['assignees'] or item['pic']},\n\n"
            f"Mohon tindak lanjut atas pekerjaan berikut:\n\n"
            f"Pekerjaan: {item['title']}\nKategori: {item['category']}\n"
            f"Prioritas: {item['priority']}\nTenggat: {item['deadline'] or 'Belum ditetapkan'}\n"
            f"Link dokumen: {item['drive_url'] or '-'}\n\nTerima kasih.")
    params = urlencode({"subject": f"Disposisi Tugas: {item['title']}", "body": body})
    return redirect(f"mailto:{recipient}?{params}")


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
