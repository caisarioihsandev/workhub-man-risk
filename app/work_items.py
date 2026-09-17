from datetime import date
from email.utils import parseaddr
from urllib.parse import urlencode

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from .db import get_db
from .decorators import login_required

bp = Blueprint(
    "work",
    __name__
)


CATEGORIES = [
    "Laporan Monitoring Perusahaan",
    "Laporan Monitoring Divisi",
    "Laporan Monitoring Cabang",
    "Laporan Monitoring Unit",
    "Kajian Risiko",
    "AOI RMI",
    "Pekerjaan Lainnya",
]


STATUSES = [
    "Belum Dimulai",
    "Dalam Proses",
    "Menunggu Review",
    "Selesai",
]


PRIORITIES = [
    "Rendah",
    "Sedang",
    "Tinggi",
    "Kritis",
]


@bp.app_context_processor
def inject_work_globals():

    return {
        "categories": CATEGORIES,
        "statuses": STATUSES,
        "priorities": PRIORITIES,
    }


@bp.get("/")
@login_required
def index():
    db = get_db()
    query = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    category = request.args.get("category", "")
    
    open_add = request.args.get("open_add") == "1"  

    sql = """
        SELECT *
        FROM work_items
        WHERE 1=1
    """

    params = []

    if query:
        sql += """
            AND (
                title LIKE ?
                OR pic LIKE ?
                OR assignees LIKE ?
                OR category LIKE ?
            )
        """

        needle = f"%{query}%"
        params.extend([needle] * 4)

    if status in STATUSES:
        sql += " AND status = ?"
        params.append(status)

    if category in CATEGORIES:
        sql += " AND category = ?"
        params.append(category)

    sql += """
        ORDER BY
            CASE
                WHEN deadline = ''
                THEN 1
                ELSE 0
            END,
            deadline,
            id DESC
    """

    items = [
        dict(row)
        for row in db.execute(
            sql,
            params
        ).fetchall()
    ]

    all_items = [
        dict(row)
        for row in db.execute(
            "SELECT * FROM work_items"
        ).fetchall()
    ]

    today = date.today().isoformat()

    for item in items:

        item["overdue"] = (
            item["status"] != "Selesai"
            and item["deadline"]
            and item["deadline"] < today
        )

    metrics = {
        "active": sum(
            i["status"] != "Selesai"
            for i in all_items
        ),

        "overdue": sum(
            i["status"] != "Selesai"
            and bool(i["deadline"])
            and i["deadline"] < today
            for i in all_items
        ),

        "review": sum(
            i["status"] == "Menunggu Review"
            for i in all_items
        ),

        "done": sum(
            i["status"] == "Selesai"
            for i in all_items
        ),

        "studies": sum(
            i["category"] == "Kajian Risiko"
            for i in all_items
        ),
    }

    status_counts = {
        s: sum(
            i["status"] == s
            for i in all_items
        )
        for s in STATUSES
    }

    return render_template(
        "dashboard/index.html",
        open_add=open_add,
        items=items,
        metrics=metrics,
        status_counts=status_counts,
        total=len(all_items),
        query=query,
        selected_status=status,
        selected_category=category,
    )


@bp.post("/items")
@login_required
def create_item():

    title = request.form.get(
        "title",
        ""
    ).strip()

    if not title:

        flash(
            "Judul pekerjaan wajib diisi.",
            "error"
        )

        return redirect(
            url_for("work.index")
        )

    category = request.form.get(
        "category",
        "Pekerjaan Lainnya"
    )

    priority = request.form.get(
        "priority",
        "Sedang"
    )

    if (
        category not in CATEGORIES
        or priority not in PRIORITIES
    ):

        flash(
            "Kategori atau prioritas tidak valid.",
            "error"
        )

        return redirect(
            url_for("work.index")
        )

    db = get_db()

    db.execute(
        """
        INSERT INTO work_items
        (
            title,
            category,
            pic,
            assignees,
            priority,
            status,
            progress,
            deadline,
            drive_url,
            notes
        )
        VALUES (
            ?, ?, ?, ?, ?,
            'Belum Dimulai',
            0, ?, ?, ?
        )
        """,
        (
            title,
            category,
            request.form.get(
                "pic",
                ""
            ).strip(),

            request.form.get(
                "assignees",
                ""
            ).strip(),

            priority,

            request.form.get(
                "deadline",
                ""
            ),

            request.form.get(
                "drive_url",
                ""
            ).strip(),

            request.form.get(
                "notes",
                ""
            ).strip(),
        ),
    )

    db.commit()
    flash("Pekerjaan berhasil ditambahkan.", "success")

    return_to = request.form.get(
        "return_to",
        "dashboard"
    )

    if return_to == "progress":
        return redirect(url_for("progress.index"))

    return redirect(url_for("work.index"))


@bp.post("/items/<int:item_id>/update")
@login_required
def update_item(item_id):
    status = request.form.get("status", "")

    try:
        progress = max(0, min(100, int(request.form.get("progress", 0))))

    except ValueError:
        progress = 0

    if status not in STATUSES:
        flash("Status tidak valid.", "error")
        return redirect(url_for("work.index"))

    if status == "Selesai":
        progress = 100

    db = get_db()

    db.execute(
        """
        UPDATE work_items
        SET
            status = ?,
            progress = ?,
            updated_at =
                CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            status,
            progress,
            item_id
        ),
    )

    db.commit()

    flash("Progres berhasil diperbarui.", "success")
    return redirect(url_for("work.index"))

@bp.post("/items/<int:item_id>/delete")
@login_required
def delete_item(item_id):
    db = get_db()
    db.execute("DELETE FROM work_items WHERE id = ?", (item_id,))
    db.commit()
    flash("Pekerjaan telah dihapus.", "success")

    return redirect(url_for("work.index"))

@bp.get("/items/<int:item_id>/email")
@login_required
def disposition_email(item_id):

    item = get_db().execute(
        """
        SELECT *
        FROM work_items
        WHERE id = ?
        """,
        (item_id,),
    ).fetchone()


    if item is None:

        flash(
            "Pekerjaan tidak ditemukan.",
            "error"
        )

        return redirect(
            url_for("progress.index")
        )


    # ==========================================
    # AMBIL EMAIL DARI FIELD ASSIGNEES
    # ==========================================

    recipient = parseaddr(
        item["assignees"] or ""
    )[1]


    # ==========================================
    # VALIDASI EMAIL
    # ==========================================

    if not recipient:

        flash(
            "Email PIC/anggota tim belum tersedia.",
            "error"
        )

        return redirect(
            url_for("progress.index")
        )


    # ==========================================
    # ISI EMAIL
    # ==========================================

    body = (
        f"Yth. "
        f"{item['assignees'] or item['pic']},\n\n"

        f"Mohon tindak lanjut atas "
        f"pekerjaan berikut:\n\n"

        f"Pekerjaan: "
        f"{item['title']}\n"

        f"Kategori: "
        f"{item['category']}\n"

        f"Prioritas: "
        f"{item['priority']}\n"

        f"Tenggat: "
        f"{item['deadline'] or 'Belum ditetapkan'}\n"

        f"Progress: "
        f"{item['progress'] or 0}%\n"

        f"Status: "
        f"{item['status']}\n"

        f"Link dokumen: "
        f"{item['drive_url'] or '-'}\n\n"

        f"Terima kasih."
    )


    # ==========================================
    # PARAMETER EMAIL
    # ==========================================

    params = urlencode({
        "view": "cm",
        "fs": "1",
        "to": recipient,
        "su": f"Disposisi Tugas: {item['title']}",
        "body": body,
    })

    return redirect(
        f"https://mail.google.com/mail/?{params}"
    )


# ============================================================
# TASK TIM
# ============================================================

@bp.get("/task-tim/")
@login_required
def team_tasks():

    db = get_db()

    query = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")

    sql = """
        SELECT *
        FROM work_items
        WHERE 1=1
    """

    params = []

    # SEARCH
    if query:

        sql += """
            AND (
                title LIKE ?
                OR pic LIKE ?
                OR assignees LIKE ?
                OR category LIKE ?
            )
        """

        needle = f"%{query}%"

        params.extend([
            needle,
            needle,
            needle,
            needle,
        ])

    # STATUS
    if status in STATUSES:

        sql += """
            AND status = ?
        """

        params.append(status)

    # PRIORITY
    if priority in PRIORITIES:

        sql += """
            AND priority = ?
        """

        params.append(priority)

    sql += """
        ORDER BY
            CASE
                WHEN deadline = ''
                THEN 1
                ELSE 0
            END,
            deadline,
            id DESC
    """

    tasks = [
        dict(row)
        for row in db.execute(
            sql,
            params
        ).fetchall()
    ]

    # ========================================================
    # METRICS
    # ========================================================

    all_tasks = [
        dict(row)
        for row in db.execute(
            """
            SELECT *
            FROM work_items
            """
        ).fetchall()
    ]

    metrics = {

        "total": len(all_tasks),

        "active": sum(
            task["status"] != "Selesai"
            for task in all_tasks
        ),

        "review": sum(
            task["status"] == "Menunggu Review"
            for task in all_tasks
        ),

        "done": sum(
            task["status"] == "Selesai"
            for task in all_tasks
        ),
    }

    return render_template(
        "team/index.html",
        tasks=tasks,
        metrics=metrics,
        query=query,
        selected_status=status,
        selected_priority=priority,
        statuses=STATUSES,
        priorities=PRIORITIES,
    )

@bp.get("/items/<int:item_id>")
@login_required
def detail(item_id):

    db = get_db()

    task = db.execute(
        """
        SELECT *
        FROM work_items
        WHERE id = ?
        """,
        (item_id,),
    ).fetchone()

    if task is None:
        flash(
            "Task tidak ditemukan.",
            "error"
        )

        return redirect(
            url_for("work.team_tasks")
        )

    return render_template(
        "team/detail.html",
        task=task
    )