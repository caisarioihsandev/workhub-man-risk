from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from .db import get_db


bp = Blueprint(
    "auth",
    __name__,
    url_prefix=""
)


# ============================================================
# LOAD USER YANG SEDANG LOGIN
# ============================================================

@bp.before_app_request
def load_logged_in_user():

    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
        return

    g.user = get_db().execute(
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

    if (
        g.user is None
        or not g.user["is_active"]
    ):
        session.clear()
        g.user = None


# ============================================================
# LOGIN
# ============================================================

@bp.route(
    "/login",
    methods=("GET", "POST")
)
def login():

    if g.user is not None:
        return redirect(
            url_for("work.index")
        )

    if request.method == "POST":

        username = (
            request.form
            .get("username", "")
            .strip()
        )

        password = request.form.get(
            "password",
            ""
        )

        db = get_db()

        user = db.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

        error = None

        if user is None:

            error = (
                "Username atau password salah."
            )

        elif not user["is_active"]:

            error = (
                "Akun Anda tidak aktif."
            )

        elif not check_password_hash(
            user["password_hash"],
            password
        ):

            error = (
                "Username atau password salah."
            )

        if error is None:

            session.clear()

            session["user_id"] = user["id"]

            next_url = request.args.get(
                "next"
            )

            if (
                next_url
                and next_url.startswith("/")
            ):
                return redirect(next_url)

            return redirect(
                url_for("work.index")
            )

        flash(
            error,
            "error"
        )

    return render_template(
        "auth/login.html"
    )


# ============================================================
# PROFIL USER
# ============================================================

@bp.route(
    "/profil",
    methods=("GET", "POST")
)
def profile():

    if g.user is None:
        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    user_id = g.user["id"]

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
        session.clear()

        return redirect(
            url_for("auth.login")
        )

    if request.method == "POST":

        full_name = (
            request.form
            .get("full_name", "")
            .strip()
        )

        username = (
            request.form
            .get("username", "")
            .strip()
        )

        email = (
            request.form
            .get("email", "")
            .strip()
        )

        if not full_name:

            flash(
                "Nama lengkap wajib diisi.",
                "error"
            )

            return render_template(
                "auth/profile.html",
                user=user
            )

        if not username:

            flash(
                "Username wajib diisi.",
                "error"
            )

            return render_template(
                "auth/profile.html",
                user=user
            )

        # ----------------------------------------------------
        # CEK USERNAME
        # ----------------------------------------------------

        existing_user = db.execute(
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

        if existing_user is not None:

            flash(
                "Username tersebut sudah digunakan oleh user lain.",
                "error"
            )

            return render_template(
                "auth/profile.html",
                user=user
            )

        # ----------------------------------------------------
        # UPDATE PROFIL
        # ----------------------------------------------------

        db.execute(
            """
            UPDATE users
            SET
                username = ?,
                full_name = ?,
                email = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                username,
                full_name,
                email,
                user_id,
            ),
        )

        db.commit()

        flash(
            "Profil berhasil diperbarui.",
            "success"
        )

        return redirect(
            url_for("auth.profile")
        )

    return render_template(
        "auth/profile.html",
        user=user
    )


# ============================================================
# GANTI PASSWORD
# ============================================================

@bp.post("/profil/password")
def change_password():

    if g.user is None:
        return redirect(
            url_for("auth.login")
        )

    current_password = request.form.get(
        "current_password",
        ""
    )

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )

    db = get_db()

    user = db.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (g.user["id"],),
    ).fetchone()

    if user is None:

        session.clear()

        return redirect(
            url_for("auth.login")
        )

    # --------------------------------------------------------
    # PASSWORD LAMA
    # --------------------------------------------------------

    if not check_password_hash(
        user["password_hash"],
        current_password
    ):

        flash(
            "Password saat ini tidak sesuai.",
            "error"
        )

        return redirect(
            url_for("auth.profile")
        )

    # --------------------------------------------------------
    # PASSWORD BARU
    # --------------------------------------------------------

    if not new_password:

        flash(
            "Password baru wajib diisi.",
            "error"
        )

        return redirect(
            url_for("auth.profile")
        )

    if len(new_password) < 6:

        flash(
            "Password baru minimal 6 karakter.",
            "error"
        )

        return redirect(
            url_for("auth.profile")
        )

    if new_password != confirm_password:

        flash(
            "Konfirmasi password tidak sama.",
            "error"
        )

        return redirect(
            url_for("auth.profile")
        )

    # --------------------------------------------------------
    # UPDATE PASSWORD
    # --------------------------------------------------------

    password_hash = generate_password_hash(
        new_password
    )

    db.execute(
        """
        UPDATE users
        SET
            password_hash = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            password_hash,
            g.user["id"],
        ),
    )

    db.commit()

    flash(
        "Password berhasil diubah.",
        "success"
    )

    return redirect(
        url_for("auth.profile")
    )


# ============================================================
# LOGOUT
# ============================================================

@bp.post("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("auth.login")
    )