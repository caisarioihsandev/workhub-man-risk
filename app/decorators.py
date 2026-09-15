from functools import wraps
from flask import flash, g, redirect, request, url_for

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(
                url_for("auth.login", next=request.path)
            )

        return view(*args, **kwargs)

    return wrapped_view


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if g.user is None:
                return redirect(
                    url_for("auth.login", next=request.path)
                )

            if g.user["role"] not in roles:
                flash(
                    "Anda tidak memiliki hak akses.",
                    "error"
                )
                return redirect(
                    url_for("work.index")
                )

            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def roles_required(*roles):
    return role_required(*roles)


def superadmin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(
                url_for("auth.login", next=request.path)
            )

        if g.user["role"] != "superadmin":
            flash(
                "Akses hanya tersedia untuk Superadmin.",
                "error"
            )
            return redirect(
                url_for("work.index")
            )

        return view(*args, **kwargs)

    return wrapped_view


def permission_required(permission):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):

            if g.user is None:
                return redirect(
                    url_for("auth.login", next=request.path)
                )

            from .permissions import has_permission

            if not has_permission(
                g.user["role"],
                permission
            ):
                flash(
                    "Anda tidak memiliki hak akses.",
                    "error"
                )

                return redirect(
                    url_for("work.index")
                )

            return view(*args, **kwargs)

        return wrapped_view

    return decorator