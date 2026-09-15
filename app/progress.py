from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for

from .db import get_db
from .decorators import permission_required


bp = Blueprint(
    "progress",
    __name__,
    url_prefix="/progress"
)


@bp.route("/")
@permission_required("work_progress")
def index():

    db = get_db()

    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    priority = request.args.get("priority", "").strip()
    pic = request.args.get("pic", "").strip()

    query = """
        SELECT *
        FROM work_items
        WHERE 1 = 1
    """

    params = []

    # =========================
    # SEARCH
    # =========================

    if q:
        query += """
            AND (
                title LIKE ?
                OR category LIKE ?
                OR pic LIKE ?
                OR assignees LIKE ?
            )
        """

        keyword = f"%{q}%"

        params.extend([
            keyword,
            keyword,
            keyword,
            keyword
        ])

    # =========================
    # STATUS
    # =========================

    if status:
        query += """
            AND status = ?
        """

        params.append(status)

    # =========================
    # PRIORITY
    # =========================

    if priority:
        query += """
            AND priority = ?
        """

        params.append(priority)

    # =========================
    # PIC
    # =========================

    if pic:
        query += """
            AND pic = ?
        """

        params.append(pic)

    query += """
        ORDER BY
            CASE
                WHEN deadline IS NULL THEN 1
                ELSE 0
            END,
            deadline ASC,
            id DESC
    """

    work_items = db.execute(
        query,
        params
    ).fetchall()

    # =========================
    # DATA SUMMARY
    # =========================

    all_items = db.execute("""
        SELECT *
        FROM work_items
    """).fetchall()

    total = len(all_items)

    belum_mulai = 0
    berjalan = 0
    selesai = 0
    terlambat = 0

    today = date.today()

    for item in all_items:

        item_status = (
            item["status"] or ""
        ).strip().lower()

        progress = item["progress"] or 0

        # -------------------------
        # STATUS
        # -------------------------

        if item_status in [
            "selesai",
            "completed",
            "done"
        ] or progress >= 100:

            selesai += 1

        elif item_status in [
            "berjalan",
            "on progress",
            "in progress",
            "proses"
        ] or progress > 0:

            berjalan += 1

        else:

            belum_mulai += 1

        # -------------------------
        # TERLAMBAT
        # -------------------------

        deadline = item["deadline"]

        if deadline and progress < 100:

            try:
                deadline_date = date.fromisoformat(
                    str(deadline)[:10]
                )

                if deadline_date < today:
                    terlambat += 1

            except ValueError:
                pass

    # =========================
    # FILTER OPTIONS
    # =========================

    statuses = db.execute("""
        SELECT DISTINCT status
        FROM work_items
        WHERE status IS NOT NULL
          AND TRIM(status) <> ''
        ORDER BY status
    """).fetchall()

    priorities = db.execute("""
        SELECT DISTINCT priority
        FROM work_items
        WHERE priority IS NOT NULL
          AND TRIM(priority) <> ''
        ORDER BY priority
    """).fetchall()

    pics = db.execute("""
        SELECT DISTINCT pic
        FROM work_items
        WHERE pic IS NOT NULL
          AND TRIM(pic) <> ''
        ORDER BY pic
    """).fetchall()

    return render_template(
        "progress/index.html",
        work_items=work_items,
        total=total,
        belum_mulai=belum_mulai,
        berjalan=berjalan,
        selesai=selesai,
        terlambat=terlambat,
        statuses=statuses,
        priorities=priorities,
        pics=pics,
        filters={
            "q": q,
            "status": status,
            "priority": priority,
            "pic": pic
        }
    )

# Work Progress
@bp.post("/<int:work_id>/status")
@permission_required("work_progress")
def update_status(work_id):

    db = get_db()

    data = request.get_json(silent=True) or {}
    status = data.get("status", "").strip()

    allowed_status = {
        "Belum Dimulai",
        "Dalam Proses",
        "Menunggu Review"
        "Selesai",
    }

    if status not in allowed_status:
        return {
            "success": False,
            "message": "Status tidak valid."
        }, 400

    item = db.execute(
        """
        SELECT id
        FROM work_items
        WHERE id = ?
        """,
        (work_id,)
    ).fetchone()

    if item is None:
        return {
            "success": False,
            "message": "Pekerjaan tidak ditemukan."
        }, 404

    # Jika pekerjaan dinyatakan selesai,
    # progress otomatis menjadi 100%.
    if status == "Selesai":

        db.execute(
            """
            UPDATE work_items
            SET status = ?,
                progress = 100,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, work_id)
        )

    # Jika dikembalikan menjadi Belum Dimulai,
    # progress otomatis menjadi 0%.
    elif status == "Belum Dimulai":

        db.execute(
            """
            UPDATE work_items
            SET status = ?,
                progress = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, work_id)
        )

    else:

        db.execute(
            """
            UPDATE work_items
            SET status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, work_id)
        )

    db.commit()

    return {
        "success": True,
        "message": "Status berhasil diperbarui."
    }

# Update Progress

@bp.post("/<int:work_id>/progress")
@permission_required("work_progress")
def update_progress(work_id):

    db = get_db()

    data = request.get_json(silent=True) or {}

    try:
        progress = int(data.get("progress", 0))
    except (TypeError, ValueError):

        return {
            "success": False,
            "message": "Nilai progress tidak valid."
        }, 400

    # Pastikan progress berada antara 0 - 100
    progress = max(0, min(100, progress))

    item = db.execute(
        """
        SELECT id
        FROM work_items
        WHERE id = ?
        """,
        (work_id,)
    ).fetchone()

    if item is None:

        return {
            "success": False,
            "message": "Pekerjaan tidak ditemukan."
        }, 404

    # Sinkronisasi status berdasarkan progress
    if progress >= 100:

        status = "Selesai"

    elif progress > 0:

        status = "Dalam Proses"

    else:

        status = "Belum Dimulai"

    db.execute(
        """
        UPDATE work_items
        SET progress = ?,
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            progress,
            status,
            work_id
        )
    )

    db.commit()

    return {
        "success": True,
        "progress": progress,
        "status": status,
        "message": "Progress berhasil diperbarui."
    }

# Edit Pekerjaan
@bp.route("/<int:work_id>/edit", methods=["GET", "POST"])
@permission_required("work_progress")
def edit(work_id):

    db = get_db()

    item = db.execute(
        """
        SELECT *
        FROM work_items
        WHERE id = ?
        """,
        (work_id,)
    ).fetchone()

    if item is None:
        return "Pekerjaan tidak ditemukan.", 404


    # ==========================================
    # SIMPAN PERUBAHAN
    # ==========================================

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        pic = request.form.get(
            "pic",
            ""
        ).strip()

        assignees = request.form.get(
            "assignees",
            ""
        ).strip()

        priority = request.form.get(
            "priority",
            ""
        ).strip()

        deadline = request.form.get(
            "deadline",
            ""
        ).strip()

        drive_url = request.form.get(
            "drive_url",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()


        # ==========================================
        # VALIDASI
        # ==========================================

        if not title:

            return render_template(
                "progress/edit.html",
                item=item,
                error="Judul pekerjaan wajib diisi."
            )


        # ==========================================
        # UPDATE DATABASE
        # ==========================================

        db.execute(
            """
            UPDATE work_items
            SET
                title = ?,
                category = ?,
                pic = ?,
                assignees = ?,
                priority = ?,
                deadline = ?,
                drive_url = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                title,
                category,
                pic,
                assignees,
                priority,
                deadline,
                drive_url,
                notes,
                work_id
            )
        )

        db.commit()

        return redirect(
            url_for("progress.index")
        )


    # ==========================================
    # FORM EDIT
    # ==========================================

    return render_template(
        "progress/edit.html",
        item=item
    )