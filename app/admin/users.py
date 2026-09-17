from functools import wraps
import sqlite3

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
    current_app,
)

from werkzeug.security import generate_password_hash


bp = Blueprint(
    "admin_users",
    __name__,
    url_prefix="/admin/users",
)


# =========================================================
# HELPER
# =========================================================

def get_db():
    """
    Membuka koneksi database.
    """

    db = sqlite3.connect(
        current_app.config["DATABASE"]
    )

    db.row_factory = sqlite3.Row

    return db


def superadmin_required(view):
    """
    Hanya Superadmin yang boleh mengakses
    Manajemen User.
    """

    @wraps(view)
    def wrapped_view(**kwargs):

        if g.user is None:
            return redirect(
                url_for(
                    "auth.login",
                    next=request.path,
                )
            )

        if g.user["role"] != "superadmin":
            flash(
                "Anda tidak memiliki hak akses.",
                "error",
            )

            return redirect(
                url_for("work.index")
            )

        return view(**kwargs)

    return wrapped_view


# =========================================================
# HELPER ROLE
# =========================================================

ROLE_LABELS = {
    "superadmin": "Superadmin",
    "user": "User",
    "vice_president": "Vice President",
}


# =========================================================
# INDEX
# =========================================================

@bp.get("/")
@superadmin_required
def index():

    db = get_db()

    users = db.execute(
        """
        SELECT
            id,
            username,
            full_name,
            email,
            role,
            is_active,
            created_at,
            updated_at
        FROM users
        ORDER BY
            CASE role
                WHEN 'superadmin' THEN 1
                WHEN 'vice_president' THEN 2
                WHEN 'user' THEN 3
                ELSE 4
            END,
            full_name COLLATE NOCASE
        """
    ).fetchall()

    db.close()

    return render_template(
        "admin/users/index.html",
        users=users,
        role_labels=ROLE_LABELS,
    )


# =========================================================
# CREATE USER
# =========================================================

@bp.route("/create", methods=("GET", "POST"))
@superadmin_required
def create():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        role = request.form.get(
            "role",
            "user"
        ).strip()

        is_active = (
            1
            if request.form.get("is_active")
            else 0
        )

        error = None

        # ---------------------------------------------
        # VALIDATION
        # ---------------------------------------------

        if not username:
            error = "Username wajib diisi."

        elif not full_name:
            error = "Nama lengkap wajib diisi."

        elif not password:
            error = "Password wajib diisi."

        elif len(password) < 8:
            error = (
                "Password minimal 8 karakter."
            )

        elif email and "@" not in email:
            error = "Format email tidak valid."

        elif role not in ROLE_LABELS:
            error = "Role tidak valid."

        if error is None:

            db = get_db()

            existing = db.execute(
                """
                SELECT id
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()

            if existing:
                error = (
                    "Username sudah digunakan."
                )

            else:

                db.execute(
                    """
                    INSERT INTO users (
                        username,
                        full_name,
                        email,
                        password_hash,
                        role,
                        is_active
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        username,
                        full_name,
                        email,
                        generate_password_hash(
                            password
                        ),
                        role,
                        is_active,
                    ),
                )

                db.commit()
                db.close()

                flash(
                    "User berhasil ditambahkan.",
                    "success",
                )

                return redirect(
                    url_for(
                        "admin_users.index"
                    )
                )

            db.close()

        flash(
            error,
            "error",
        )

    return render_template(
        "admin/users/create.html",
        role_labels=ROLE_LABELS,
    )


# =========================================================
# EDIT USER
# =========================================================

@bp.route("/<int:user_id>/edit", methods=("GET", "POST"))
@superadmin_required
def edit(user_id):

    db = get_db()

    user = db.execute(
        """
        SELECT
            id,
            username,
            full_name,
            email,
            role,
            is_active
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()

    if user is None:

        db.close()

        flash(
            "User tidak ditemukan.",
            "error",
        )

        return redirect(
            url_for("admin_users.index")
        )

    if request.method == "POST":

        # -------------------------------------------------
        # AMBIL DATA FORM
        # -------------------------------------------------

        username = request.form.get(
            "username",
            "",
        ).strip()

        full_name = request.form.get(
            "full_name",
            "",
        ).strip()

        email = request.form.get(
            "email",
            "",
        ).strip()

        role = request.form.get(
            "role",
            "user",
        ).strip()

        password = request.form.get(
            "password",
            "",
        )

        is_active = (
            1
            if request.form.get("is_active")
            else 0
        )

        error = None

        # -------------------------------------------------
        # VALIDASI
        # -------------------------------------------------

        if not username:

            error = "Username wajib diisi."

        elif not full_name:

            error = "Nama lengkap wajib diisi."

        elif role not in ROLE_LABELS:

            error = "Role tidak valid."

        elif password and len(password) < 8:

            error = (
                "Password minimal 8 karakter."
            )

        # -------------------------------------------------
        # CEK FORMAT EMAIL
        # -------------------------------------------------

        elif email and "@" not in email:

            error = "Format email tidak valid."

        # -------------------------------------------------
        # CEK USERNAME DUPLIKAT
        # -------------------------------------------------

        if error is None:

            existing_username = db.execute(
                """
                SELECT id
                FROM users
                WHERE username = ?
                  AND id != ?
                """,
                (
                    username,
                    user_id,
                ),
            ).fetchone()

            if existing_username:

                error = (
                    "Username sudah digunakan "
                    "oleh user lain."
                )

        # -------------------------------------------------
        # JANGAN NONAKTIFKAN DIRI SENDIRI
        # -------------------------------------------------

        if (
            error is None
            and user["id"] == g.user["id"]
            and not is_active
        ):

            error = (
                "Anda tidak dapat menonaktifkan "
                "akun sendiri."
            )

        # -------------------------------------------------
        # JANGAN MENGHILANGKAN SUPERADMIN TERAKHIR
        # -------------------------------------------------

        if (
            error is None
            and user["role"] == "superadmin"
        ):

            changing_from_superadmin = (
                role != "superadmin"
            )

            deactivating = (
                not is_active
            )

            if (
                changing_from_superadmin
                or deactivating
            ):

                active_superadmins = db.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM users
                    WHERE
                        role = 'superadmin'
                        AND is_active = 1
                        AND id != ?
                    """,
                    (user_id,),
                ).fetchone()["total"]

                if active_superadmins == 0:

                    error = (
                        "Minimal harus ada satu "
                        "Superadmin aktif."
                    )

        # -------------------------------------------------
        # UPDATE
        # -------------------------------------------------

        if error is None:

            if password:

                db.execute(
                    """
                    UPDATE users
                    SET
                        username = ?,
                        full_name = ?,
                        email = ?,
                        password_hash = ?,
                        role = ?,
                        is_active = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        username,
                        full_name,
                        email,
                        generate_password_hash(
                            password
                        ),
                        role,
                        is_active,
                        user_id,
                    ),
                )

            else:

                db.execute(
                    """
                    UPDATE users
                    SET
                        username = ?,
                        full_name = ?,
                        email = ?,
                        role = ?,
                        is_active = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        username,
                        full_name,
                        email,
                        role,
                        is_active,
                        user_id,
                    ),
                )

            db.commit()
            db.close()

            flash(
                "Data user berhasil diperbarui.",
                "success",
            )

            return redirect(
                url_for(
                    "admin_users.index"
                )
            )

        # -------------------------------------------------
        # TAMPILKAN ERROR
        # -------------------------------------------------

        flash(
            error,
            "error",
        )

    db.close()

    return render_template(
        "admin/users/edit.html",
        user=user,
        role_labels=ROLE_LABELS,
    )

# =========================================================
# TOGGLE STATUS
# =========================================================

@bp.post("/<int:user_id>/toggle")
@superadmin_required
def toggle(user_id):

    db = get_db()

    user = db.execute(
        """
        SELECT
            id,
            username,
            role,
            is_active
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()

    if user is None:

        db.close()

        flash(
            "User tidak ditemukan.",
            "error",
        )

        return redirect(
            url_for(
                "admin_users.index"
            )
        )

    # Tidak boleh menonaktifkan diri sendiri

    if user["id"] == g.user["id"]:

        db.close()

        flash(
            "Anda tidak dapat menonaktifkan "
            "akun sendiri.",
            "error",
        )

        return redirect(
            url_for(
                "admin_users.index"
            )
        )

    new_status = (
        0
        if user["is_active"]
        else 1
    )

    # Pastikan selalu ada Superadmin aktif

    if (
        user["role"] == "superadmin"
        and new_status == 0
    ):

        active_superadmins = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM users
            WHERE
                role = 'superadmin'
                AND is_active = 1
                AND id != ?
            """,
            (user_id,),
        ).fetchone()["total"]

        if active_superadmins == 0:

            db.close()

            flash(
                "Minimal harus ada satu "
                "Superadmin aktif.",
                "error",
            )

            return redirect(
                url_for(
                    "admin_users.index"
                )
            )

    db.execute(
        """
        UPDATE users
        SET
            is_active = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            new_status,
            user_id,
        ),
    )

    db.commit()
    db.close()

    if new_status:

        flash(
            "User berhasil diaktifkan.",
            "success",
        )

    else:

        flash(
            "User berhasil dinonaktifkan.",
            "success",
        )

    return redirect(
        url_for(
            "admin_users.index"
        )
    )