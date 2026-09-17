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
    "documents",
    __name__,
    url_prefix="/dokumen"
)


DOCUMENT_TYPES = [
    "Pedoman",
    "SOP",
    "Monitoring Risiko",
    "Kajian Risiko",
    "Regulasi",
    "Surat",
    "Formulir",
    "Lainnya",
]


@bp.app_context_processor
def inject_document_globals():

    return {
        "document_types": DOCUMENT_TYPES,
    }


# ============================================================
# DAFTAR DOKUMEN
# ============================================================

@bp.route("/")
@permission_required("documents")
def index():

    db = get_db()

    query = request.args.get(
        "q",
        ""
    ).strip()

    document_type = request.args.get(
        "document_type",
        ""
    ).strip()

    sql = """
        SELECT *
        FROM documents
        WHERE 1=1
    """

    params = []

    if query:

        sql += """
            AND (
                name LIKE ?
                OR document_type LIKE ?
            )
        """

        needle = f"%{query}%"

        params.extend([
            needle,
            needle,
        ])

    if document_type in DOCUMENT_TYPES:

        sql += """
            AND document_type = ?
        """

        params.append(document_type)

    sql += """
        ORDER BY
            id DESC
    """

    documents = db.execute(
        sql,
        params
    ).fetchall()

    return render_template(
        "documents/index.html",
        documents=documents,
        query=query,
        selected_type=document_type,
    )


# ============================================================
# TAMBAH DOKUMEN
# ============================================================

@bp.route(
    "/create",
    methods=("GET", "POST")
)
@permission_required("documents")
def create():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        document_type = request.form.get(
            "document_type",
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
                "documents/create.html"
            )

        if not document_type:

            flash(
                "Jenis dokumen wajib dipilih.",
                "error"
            )

            return render_template(
                "documents/create.html"
            )

        if not drive_url:

            flash(
                "Link Google Drive wajib diisi.",
                "error"
            )

            return render_template(
                "documents/create.html"
            )

        if document_type not in DOCUMENT_TYPES:

            flash(
                "Jenis dokumen tidak valid.",
                "error"
            )

            return render_template(
                "documents/create.html"
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
                document_type,
                drive_url,
            ),
        )

        db.commit()

        flash(
            "Dokumen berhasil ditambahkan.",
            "success"
        )

        return redirect(
            url_for("documents.index")
        )

    return render_template(
        "documents/create.html"
    )


# ============================================================
# EDIT DOKUMEN
# ============================================================

@bp.route(
    "/<int:document_id>/edit",
    methods=("GET", "POST")
)
@permission_required("documents")
def edit(document_id):

    db = get_db()

    document = db.execute(
        """
        SELECT *
        FROM documents
        WHERE id = ?
        """,
        (document_id,)
    ).fetchone()

    if document is None:
        abort(404)

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        document_type = request.form.get(
            "document_type",
            ""
        ).strip()

        drive_url = request.form.get(
            "drive_url",
            ""
        ).strip()

        if not name or not document_type or not drive_url:

            flash(
                "Nama, jenis, dan link dokumen wajib diisi.",
                "error"
            )

            return render_template(
                "documents/edit.html",
                document=document
            )

        if document_type not in DOCUMENT_TYPES:

            flash(
                "Jenis dokumen tidak valid.",
                "error"
            )

            return render_template(
                "documents/edit.html",
                document=document
            )

        db.execute(
            """
            UPDATE documents
            SET
                name = ?,
                document_type = ?,
                drive_url = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                name,
                document_type,
                drive_url,
                document_id,
            ),
        )

        db.commit()

        flash(
            "Dokumen berhasil diperbarui.",
            "success"
        )

        return redirect(
            url_for("documents.index")
        )

    return render_template(
        "documents/edit.html",
        document=document
    )


# ============================================================
# HAPUS DOKUMEN
# ============================================================

@bp.post(
    "/<int:document_id>/delete"
)
@permission_required("documents")
def delete(document_id):

    db = get_db()

    document = db.execute(
        """
        SELECT id
        FROM documents
        WHERE id = ?
        """,
        (document_id,)
    ).fetchone()

    if document is None:
        abort(404)

    db.execute(
        """
        DELETE FROM documents
        WHERE id = ?
        """,
        (document_id,)
    )

    db.commit()

    flash(
        "Dokumen berhasil dihapus.",
        "success"
    )

    return redirect(
        url_for("documents.index")
    )