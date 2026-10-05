from sqlite_database import init_and_seed_db
from sqlmodel import Session, create_engine

DATABASE_URL = "sqlite:///database.db"

init_and_seed_db()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def get_session():
    with Session(engine) as session:
        yield session
