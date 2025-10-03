from sqlmodel import create_engine, Session
from .config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)

def get_session():
    # FastAPI expects a generator dependency that yields the session.
    with Session(engine) as session:
        yield session
