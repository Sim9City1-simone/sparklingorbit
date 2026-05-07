from sqlmodel import SQLModel, create_engine
from config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


def init_db():
    SQLModel.metadata.create_all(engine)
