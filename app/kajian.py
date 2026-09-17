from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    abort,
)

from .db import get_db
from .decorators import permission_required


bp = Blueprint(
    "kajian",
    __name__,
    url_prefix="/kajian-risiko"
)


KAJIAN_DOCUMENT_TYPE = "Kajian Risiko"


# ============================================================
# DAFTAR DOKUMEN KAJIAN RISIKO
# ============================================================

@bp.route("/")
@permission_required("risk_assessment")
def index():

    db = get_db()

    query = request.args.get(
        "q",
        ""
    ).strip()

    sql = """
        SELECT *
        FROM documents
        WHERE document_type = ?
    """

    params = [
        KAJIAN_DOCUMENT_TYPE
    ]

    if query:

        sql += """
            AND name LIKE ?
        """

        params.append(
            f"%{query}%"
        )

    sql += """
        ORDER BY id DESC
    """

    documents = db.execute(
        sql,
        params
    ).fetchall()

    return render_template(
        "kajian/index.html",
        documents=documents,
        query=query,
    )


# ============================================================
# TAMBAH DOKUMEN KAJIAN RISIKO
# ============================================================

@bp.route(
    "/create",
    methods=("GET", "POST")
)
@permission_required("risk_assessment")
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
                "kajian/create.html"
            )

        if not drive_url:

            flash(
                "Link Google Drive wajib diisi.",
                "error"
            )

            return render_template(
                "kajian/create.html"
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
                KAJIAN_DOCUMENT_TYPE,
                drive_url,
            ),
        )

        db.commit()

        flash(
            "Dokumen kajian risiko berhasil ditambahkan.",
            "success"
        )

        return redirect(
            url_for("kajian.index")
        )

    return render_template(
        "kajian/create.html"
    )


# ============================================================
# EDIT DOKUMEN KAJIAN RISIKO
# ============================================================

@bp.route(
    "/<int:document_id>/edit",
    methods=("GET", "POST")
)
@permission_required("risk_assessment")
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
            KAJIAN_DOCUMENT_TYPE,
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
                "kajian/edit.html",
                document=document
            )

        if not drive_url:

            flash(
                "Link Google Drive wajib diisi.",
                "error"
            )

            return render_template(
                "kajian/edit.html",
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
                KAJIAN_DOCUMENT_TYPE,
            ),
        )

        db.commit()

        flash(
            "Dokumen kajian risiko berhasil diperbarui.",
            "success"
        )

        return redirect(
            url_for("kajian.index")
        )

    return render_template(
        "kajian/edit.html",
        document=document
    )


# ============================================================
# HAPUS DOKUMEN KAJIAN RISIKO
# ============================================================

@bp.post(
    "/<int:document_id>/delete"
)
@permission_required("risk_assessment")
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
            KAJIAN_DOCUMENT_TYPE,
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
            KAJIAN_DOCUMENT_TYPE,
        )
    )

    db.commit()

    flash(
        "Dokumen kajian risiko berhasil dihapus.",
        "success"
    )

    return redirect(
        url_for("kajian.index")
    )