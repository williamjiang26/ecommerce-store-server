import strawberry
from typing import Optional
from dotenv import load_dotenv

from dotenv import load_dotenv
from sqlmodel import SQLModel, Field 
load_dotenv()


# SQLModel DB Table Definition (Acts as both SQLAlchemy table and Pydantic validation)
class EssayTable(SQLModel, table=True):
    __tablename__ = "essays"
    id: Optional[int] = Field(default=None, primary_key=True)

    date: str = Field(nullable=False)
    title: str
    content: Optional[str] = Field(default=None)
@strawberry.type
class Essay:
    id: int
    date: str
    title: str
    content: Optional[str] = None
 
