from functools import wraps
from flask import flash, g, redirect, request, url_for

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped_view


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if g.user is None:
                return redirect(url_for("auth.login", next=request.path))
            if g.user["role"] not in roles:
                flash("Anda tidak memiliki hak akses.", "error")
                return redirect(url_for("work.index"))
            return view(*args, **kwargs)
        return wrapped_view
    return decorator