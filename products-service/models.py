import strawberry
from typing import Optional
from dotenv import load_dotenv


from sqlmodel import SQLModel, Field 
load_dotenv()


# SQLModel DB Table Definition (Acts as both SQLAlchemy table and Pydantic validation)
class ProductTable(SQLModel, table=True):
    __tablename__ = "products"
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(nullable=False)
    stock: bool
    price: int
    img: str
    priceId: Optional[str] = Field(default=None)
@strawberry.type
class Product:
    id: int
    name: str

    stock: bool
    price: int
    priceId: Optional[str] = None
    img: Optional[str] = None
