from flask import Blueprint, flash, redirect, render_template, request, url_for, abort
from .db import get_db
from .decorators import permission_required

bp = Blueprint("monitoring", __name__, url_prefix="/monitoring")

MONITORING_DOCUMENT_TYPE = "Monitoring Risiko"

# ============================================================
# DAFTAR DOKUMEN MONITORING RISIKO
# ============================================================

@bp.route("/")
@permission_required("risk_monitoring")
def index():
    db = get_db()
    query = request.args.get("q", "").strip()

    sql = "SELECT * FROM documents WHERE document_type = ?"
    params = [MONITORING_DOCUMENT_TYPE]

    if query:
        sql += " AND name LIKE ?"
        params.append(f"%{query}%")

    sql += " ORDER BY id DESC"
    documents = db.execute(sql, params).fetchall()
    return render_template("monitoring/index.html", documents=documents, query=query)


# ============================================================
# TAMBAH DOKUMEN MONITORING RISIKO
# ============================================================

@bp.route(
    "/create",
    methods=("GET", "POST")
)
@permission_required("risk_monitoring")
def create():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        drive_url = request.form.get(
            "drive_url",
            ""
        ).strip()

        if not name:

            flash(
                "Nama dokumen wajib diisi.",
                "error"
            )

            return render_template(
                "monitoring/create.html"
            )

        if not drive_url:

            flash(
                "Link Google Drive wajib diisi.",
                "error"
            )

            return render_template(
                "monitoring/create.html"
            )

        db = get_db()

        db.execute(
            """
            INSERT INTO documents (
                name,
                document_type,
                drive_url
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                MONITORING_DOCUMENT_TYPE,
                drive_url,
            ),
        )

        db.commit()

        flash(
            "Dokumen monitoring risiko berhasil ditambahkan.",
            "success"
        )

        return redirect(
            url_for("monitoring.index")
        )

    return render_template(
        "monitoring/create.html"
    )


# ============================================================
# EDIT DOKUMEN MONITORING RISIKO
# ============================================================

@bp.route(
    "/<int:document_id>/edit",
    methods=("GET", "POST")
)
@permission_required("risk_monitoring")
def edit(document_id):

    db = get_db()

    document = db.execute(
        """
        SELECT *
        FROM documents
        WHERE id = ?
          AND document_type = ?
        """,
        (
            document_id,
            MONITORING_DOCUMENT_TYPE,
        )
    ).fetchone()

    if document is None:
        abort(404)

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        drive_url = request.form.get(
            "drive_url",
            ""
        ).strip()

        if not name:

            flash(
                "Nama dokumen wajib diisi.",
                "error"
            )

            return render_template(
                "monitoring/edit.html",
                document=document
            )

        if not drive_url:

            flash(
                "Link Google Drive wajib diisi.",
                "error"
            )

            return render_template(
                "monitoring/edit.html",
                document=document
            )

        db.execute(
            """
            UPDATE documents
            SET
                name = ?,
                drive_url = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND document_type = ?
            """,
            (
                name,
                drive_url,
                document_id,
                MONITORING_DOCUMENT_TYPE,
            ),
        )

        db.commit()

        flash(
            "Dokumen monitoring risiko berhasil diperbarui.",
            "success"
        )

        return redirect(
            url_for("monitoring.index")
        )

    return render_template(
        "monitoring/edit.html",
        document=document
    )


# ============================================================
# HAPUS DOKUMEN MONITORING RISIKO
# ============================================================

@bp.post(
    "/<int:document_id>/delete"
)
@permission_required("risk_monitoring")
def delete(document_id):

    db = get_db()

    document = db.execute(
        """
        SELECT id
        FROM documents
        WHERE id = ?
          AND document_type = ?
        """,
        (
            document_id,
            MONITORING_DOCUMENT_TYPE,
        )
    ).fetchone()

    if document is None:
        abort(404)

    db.execute(
        """
        DELETE FROM documents
        WHERE id = ?
          AND document_type = ?
        """,
        (
            document_id,
            MONITORING_DOCUMENT_TYPE,
        )
    )

    db.commit()

    flash(
        "Dokumen monitoring risiko berhasil dihapus.",
        "success"
    )

    return redirect(
        url_for("monitoring.index")
    )