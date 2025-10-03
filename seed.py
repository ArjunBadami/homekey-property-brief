from sqlmodel import SQLModel, Session, select
from sqlalchemy import func
from app.deps import engine
from app.models import Item

def run():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        total = s.exec(select(func.count()).select_from(Item)).one()
        if total == 0:
            s.add_all([Item(title=f"Note {i}", body="lorem ipsum") for i in range(1, 11)])
            s.commit()

if __name__ == "__main__":
    run()
