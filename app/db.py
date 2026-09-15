import sqlite3
from pathlib import Path
from flask import current_app, g

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    schema_path = (Path(current_app.root_path).parent / "schema.sql")
    db.executescript(schema_path.read_text(encoding="utf-8"))
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        print("Database Workhub berhasil dibuat.")