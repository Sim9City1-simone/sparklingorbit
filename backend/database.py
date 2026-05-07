from sqlmodel import SQLModel, create_engine, text
from config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


def init_db():
    SQLModel.metadata.create_all(engine)
    _migrate()


def _migrate():
    """Run simple additive column migrations for SQLite."""
    with engine.connect() as conn:
        # Add creator_id to job table if missing
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(job)")).fetchall()}
        if "creator_id" not in cols:
            conn.execute(text("ALTER TABLE job ADD COLUMN creator_id TEXT"))
            conn.commit()
