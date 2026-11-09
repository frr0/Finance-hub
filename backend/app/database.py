import os
from typing import Generator
from sqlmodel import SQLModel, Session, create_engine

DATABASE_DIR = os.getenv("DATABASE_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(DATABASE_DIR, 'financehub.db')}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False
)

def init_db(target_engine=None):
    use_engine = target_engine or engine
    SQLModel.metadata.create_all(use_engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
