from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="")

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
        return

    g.user = get_db().execute(
        """
        SELECT id, username, full_name, email, role, is_active
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()

    if (g.user is None or not g.user["is_active"]):
        session.clear()
        g.user = None

@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user is not None:
        return redirect(url_for("work.index"))

    if request.method == "POST":
        username = (request.form.get("username", "").strip())
        password = request.form.get("password", "")

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
            error = ("Username atau password salah.")

        elif not user["is_active"]:
            error = ("Akun Anda tidak aktif.")

        elif not check_password_hash(user["password_hash"], password):
            error = ("Username atau password salah.")

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            next_url = request.args.get("next")

            if (next_url and next_url.startswith("/")):
                return redirect(next_url)
            return redirect(url_for("work.index"))
        flash(error, "error")

    return render_template("auth/login.html")


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))