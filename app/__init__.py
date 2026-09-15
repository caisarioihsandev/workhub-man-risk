import os
from pathlib import Path

from flask import Flask

# =========================================================
# PROJECT DIRECTORY
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# APPLICATION FACTORY
# =========================================================

def create_app():

    app = Flask(
        __name__,

        # Template berada di:
        # workhub-man-risk/templates
        template_folder=str(
            BASE_DIR / "templates"
        ),

        # Static berada di:
        # workhub-man-risk/static
        static_folder=str(
            BASE_DIR / "static"
        ),
    )


    # =====================================================
    # CONFIGURATION
    # =====================================================

    app.config.from_mapping(
    SECRET_KEY=os.environ.get("SECRET_KEY", "change-this-in-production"),
    DATABASE=os.environ.get(
        "DATABASE_PATH",
        str(BASE_DIR / "workhub.db")
    ),
)


    # =====================================================
    # DATABASE
    # =====================================================

    from . import db

    db.init_app(app)


    # =====================================================
    # AUTHENTICATION
    # =====================================================

    from .auth import bp as auth_bp

    app.register_blueprint(
        auth_bp
    )


    # =====================================================
    # WORK ITEMS
    # =====================================================

    from .work_items import bp as work_bp

    app.register_blueprint(
        work_bp
    )


    # =====================================================
    # ADMIN / USER MANAGEMENT
    # =====================================================

    from .admin import users_bp

    app.register_blueprint(
        users_bp
    )

    # =====================================================
    # PERMISSIONS
    # =====================================================

    from .permissions import has_permission

    app.jinja_env.globals[
        "has_permission"
    ] = has_permission

    # =====================================================
    # PROGRESS
    # =====================================================

    from . import progress

    app.register_blueprint(
        progress.bp
    )

    return app