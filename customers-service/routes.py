from fastapi import APIRouter
from sqlmodel import SQLModel, Field, create_engine, Session, select, delete
import os

from dotenv import load_dotenv
from models import Customer, Orders, Account, AccountTable
load_dotenv()

DATABASE_URL = os.getenv("CUSTOMER_DATABASE_URL")
# Create the async engine
engine = create_engine(DATABASE_URL, echo=True)


# SQLModel DB Table Definition (Acts as both SQLAlchemy table and Pydantic validation)
class CustomerTable(SQLModel, table=True):
    __tablename__ = "customers"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)


# functions
# get customer
def get_customer(id: int):
    with Session(engine) as session:
        customer = session.get(CustomerTable, id)
        return customer

# get customers
def get_customers():
    with Session(engine) as session:
        statement = select(CustomerTable)
        db_customers = session.exec(statement).all()
        return db_customers



# post customer - create new user
def post_customer(id: int, account_info: Account):
    with Session(engine) as session:   
        customer = session.get(CustomerTable, account_info.email)
        if not customer:
            db_account = AccountTable(
            email=account_info.email,

            customer_id=id 
        )
        new_row = CustomerTable(id=id, account_info=db_account)
        session.add(new_row)
        session.commit()
        statement = select(CustomerTable)
        db_customers = session.exec(statement).all()
        return db_customers



# update customer
def update_customer(id, account_info: Account, orders: Orders):
    with Session(engine) as session:
        update_customer = session.get(CustomerTable, id)
        if not update_customer:
            return session.exec(select(CustomerTable)).all()
        update_customer.account_info = account_info
        if orders:

            if orders.isPurchased:
                update_customer.orders.append(orders)
                if orders.id in update_customer.shopping_bag:
                    update_customer.shopping_bag.remove(orders.id)
            else:
                if orders.id not in update_customer.shopping_bag:
                    update_customer.shopping_bag.append(orders)
        session.add(update_customer)
        session.commit()

        statement = select(CustomerTable)
        db_customers = session.exec(statement).all()
        return db_customers
# delete customer
def delete_customer(id: int):
    with Session(engine) as session:
        customer_to_delete = session.get(CustomerTable, id)
        if customer_to_delete:
            session.delete(customer_to_delete)
            session.commit()

        statement = select(CustomerTable)
        db_customers = session.exec(statement).all()
        return db_customers
# delete many
def delete_all_customers():
    with Session(engine) as session:
        statement = delete(CustomerTable)
        session.exec(statement)

        session.commit()

        return []

# rest endpoints
api_router = APIRouter(prefix="/api", tags=["customers"])




def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@api_router.on_event("startup")
def on_startup():
    create_db_and_tables()



@api_router.get("/check")
def health_check():
    return {"status": "healthy", "service": "customer-service"}
