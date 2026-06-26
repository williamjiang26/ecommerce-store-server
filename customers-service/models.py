import strawberry
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()
from sqlmodel import SQLModel, Field , Relationship
@strawberry.type
class Account:
    id: int
    email: str




@strawberry.type
class Orders:
    id: int
    productId: int
    isPurchased: bool





@strawberry.type
class Customer:
    id: int
    account_information: Account
    shopping_cart: List[Orders]
    orders: List[Orders]

class AccountTable(SQLModel, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    customer_id: int = Field(foreign_key="customers.id")
    customer: "CustomerTable" = Relationship(back_populates="account_information")

class OrderTable(SQLModel, table=True):
    __tablename__ = "orders"
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int

    is_purchased: bool
    # Foreign keys to distinguish between cart items and past orders
    cart_customer_id: Optional[int] = Field(default=None, foreign_key="customers.id")
    order_customer_id: Optional[int] = Field(default=None, foreign_key="customers.id")

class CustomerTable(SQLModel, table=True):
    __tablename__ = "customers"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Fix: Replaced invalid List[Orders] column assignments with database relationships
    account_information: AccountTable = Relationship(
        back_populates="customer", 
        sa_relationship_kwargs={"uselist": False} # Ensures 1-to-1 relationship
    )
    shopping_cart: List[OrderTable] = Relationship(
        sa_relationship_kwargs={"primaryjoin": "CustomerTable.id==OrderTable.cart_customer_id"}
    )
    orders: List[OrderTable] = Relationship(
        sa_relationship_kwargs={"primaryjoin": "CustomerTable.id==OrderTable.order_customer_id"}
    )