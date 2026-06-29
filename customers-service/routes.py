from fastapi import APIRouter, HTTPException, status
from sqlmodel import SQLModel, Field, create_engine, Session, select, delete
import os

from dotenv import load_dotenv
from models import Customer, Orders, OrdersInput, AccountInput, AccountTable, CustomerTable, OrderTable
load_dotenv()
from sqlalchemy.orm import joinedload
DATABASE_URL = os.getenv("CUSTOMER_DATABASE_URL")
# Create the async engine
engine = create_engine(DATABASE_URL, echo=True)




# functions
# get customer
def get_customer(id: int):
   with Session(engine) as session: 
        statement = (
            select(CustomerTable)
            .where(CustomerTable.id == id)
            .options(
                joinedload(CustomerTable.account_information),
                joinedload(CustomerTable.orders),
                joinedload(CustomerTable.shopping_cart)
            )
        )
        # use grpc to get the product details
        customer = session.exec(statement).unique().first()
        return customer

# get customers
def get_customers():
    with Session(engine) as session:
        statement = (
            select(CustomerTable)
            .options(
                joinedload(CustomerTable.account_information),
                joinedload(CustomerTable.orders),
                joinedload(CustomerTable.shopping_cart)
            )
        )
        db_customers = session.exec(statement).unique().all()
        return db_customers

# post customer - create new user
def post_customer(account_information: AccountInput):
    with Session(engine) as session:  
  

        existing_account = session.exec(
            select(AccountTable).where(AccountTable.email == account_information.email)
        ).first()
        if existing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists."
            ) 
        new_row = CustomerTable()
        db_account = AccountTable(
            email=account_information.email,
            customer=new_row 
        )
        new_row.account_information = db_account
        session.add(new_row)
        session.commit()
        session.refresh(new_row)
        statement = (
            select(CustomerTable)
            .options(
                joinedload(CustomerTable.account_information),
                joinedload(CustomerTable.orders),
                joinedload(CustomerTable.shopping_cart)
            )
        )
        db_customers = session.exec(statement).unique().all()
        return db_customers

# update customer
def update_customer_orders(account_information: AccountInput, orders: OrdersInput):
    with Session(engine) as session:
        account = session.exec(select(AccountTable).where(AccountTable.email == account_information.email)).first()
        update_customer = session.get(CustomerTable, account.customer_id)
        if not update_customer:
            return session.exec(select(CustomerTable)).unique().all()
        order = OrderTable(product_id=orders.productId, is_purchased=orders.isPurchased)
        if orders.isPurchased:
            order.order_customer_id = update_customer.id
            order.cart_customer_id = None
        else:
            similar_orders = [o for o in update_customer.shopping_cart if order.product_id == o.product_id]
            print(similar_orders)
            if len([o.cart_customer_id for o in similar_orders if update_customer.id == o.cart_customer_id]) == 0:
                order.cart_customer_id = update_customer.id
                order.order_customer_id = None
            else:
                return ValueError("already in cart")
        session.add(order)
        session.commit()
        session.expire_all() 
        statement = (
            select(CustomerTable)
            .options(
                joinedload(CustomerTable.account_information),
                joinedload(CustomerTable.orders),
                joinedload(CustomerTable.shopping_cart)
            )
        )
        db_customers = session.exec(statement).unique().all()
        return db_customers

def update_customer_information(account_information: AccountInput):
    with Session(engine) as session:
        account = session.exec(select(AccountTable).where(AccountTable.email == account_information.email)).first()
        update_customer = session.get(CustomerTable, account.customer_id)
        if not update_customer:
            return session.exec(select(CustomerTable)).all() 
        update_customer.account_information = account_information # update necessary fields only no email
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

# delete many
def delete_order_cart(account_information: AccountInput, orders: OrdersInput):
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