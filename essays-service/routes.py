import os
from fastapi import APIRouter
from typing import List, Optional

from sqlmodel import SQLModel, Session, create_engine, delete, select
from models import EssayTable

DATABASE_URL = os.getenv("ESSAY_DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

# 1. Fetch single essay by integer ID
def get_essay(id: int) -> Optional[EssayTable]:
    with Session(engine) as session:
        return session.get(EssayTable, id)

# 2. Fetch all essays
def get_essays() -> List[EssayTable]:
    with Session(engine) as session:
        statement = select(EssayTable)
        return list(session.exec(statement).all())

# 3. Create a new essay and return updated list
def post_essay(date: str, title: str, content: Optional[str] = None) -> List[EssayTable]:
    with Session(engine) as session:
        new_row = EssayTable(date=date, title=title, content=content)
        session.add(new_row)
        session.commit()
        
        statement = select(EssayTable)
        return list(session.exec(statement).all())

# 4. Update an existing essay and return updated list
def update_essay(id: int, date: str, title: str, content: Optional[str] = None) -> List[EssayTable]:
    with Session(engine) as session:
        # Avoided function variable name collision/shadowing
        db_essay = session.get(EssayTable, id)
        
        if not db_essay:
            statement = select(EssayTable)
            return list(session.exec(statement).all())
            
        db_essay.date = date
        db_essay.title = title
        db_essay.content = content
        
        session.add(db_essay)
        session.commit()
        
        statement = select(EssayTable)
        return list(session.exec(statement).all())

# 5. Delete an essay and return remaining list
def delete_essay(id: int) -> List[EssayTable]:
    with Session(engine) as session:
        essay_to_delete = session.get(EssayTable, id)
        if essay_to_delete:
            session.delete(essay_to_delete)
            session.commit()
            
        statement = select(EssayTable)
        return list(session.exec(statement).all())

# 6. Clear out all rows
def delete_all_essays() -> List[EssayTable]:
    with Session(engine) as session:
        statement = delete(EssayTable)
        session.exec(statement)
        session.commit()
        return []

api_router = APIRouter(prefix="/api", tags=["Essays"])
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@api_router.on_event("startup")
def on_startup():
    create_db_and_tables()