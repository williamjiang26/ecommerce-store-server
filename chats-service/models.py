from dotenv import load_dotenv
import os
load_dotenv()

import strawberry
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine


DATABASE_URL = os.getenv("MESSAGE_DATABASE_URL")
# Create the async engine
engine = create_engine(DATABASE_URL, echo=True)


class MessageTable(SQLModel, table=True):
    __tablename__ = "messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    sender_type: str = Field(nullable=False)
    sender_name: str = Field(nullable=False)
    text: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


@strawberry.type
class Message:
    id: str
    sender_type: str
    sender_name: str
    text: str


def init_db():
    SQLModel.metadata.create_all(engine)
