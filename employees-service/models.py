import strawberry
import os
from dotenv import load_dotenv

from typing import Optional
from sqlmodel import SQLModel, Field, create_engine

load_dotenv()
DATABASE_URL = os.getenv("EMPLOYEE_DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)


class EmployeeTable(SQLModel, table=True):
    __tablename__ = "employees"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    cognitoId: str = Field(nullable=False, unique=True, index=True)
    userRole: str = Field(nullable=False)
    storeId: Optional[int] = Field(default=None, nullable=True)
    email: Optional[str] = Field(default="", nullable=True)
    phoneNumber: Optional[str] = Field(default="", nullable=True)
    img: Optional[str] = Field(default=None, nullable=True)


@strawberry.type
class Employee:
    id: int
    name: str
    cognitoId: str
    storeId: Optional[int] = None
    userRole: str
    email: Optional[str] = ""
    phoneNumber: Optional[str] = ""

    img: Optional[str] = None
