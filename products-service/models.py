import strawberry
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@strawberry.type
class Product:
    id: int
    name: str
    img: Optional[str] = None
