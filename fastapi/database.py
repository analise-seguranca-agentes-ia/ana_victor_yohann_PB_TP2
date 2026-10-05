from sqlite_database import DATABASE_PATH, init_and_seed_db
from sqlmodel import Session, create_engine

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

init_and_seed_db()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def get_session():
    with Session(engine) as session:
        yield session
