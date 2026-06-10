import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import APIRouter
from sqlmodel import SQLModel, Field, create_engine, Session, select, delete

ORDER_DATABASE_URL = os.getenv("ORDER_DATABASE_URL")
# Create the async engine
engine = create_engine(ORDER_DATABASE_URL, echo=True)


# SQLModel DB Table Definition (Acts as both SQLAlchemy table and Pydantic validation)
class OrderTable(SQLModel, table=True):
    __tablename__ = "orders"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)


# functions
# get order
def get_order(id: int):
    with Session(engine) as session:
        order = session.get(OrderTable, id)
        return order


# get orders
def get_orders():
    with Session(engine) as session:
        statement = select(OrderTable)
        db_orders = session.exec(statement).all()
        return db_orders


# post order
def post_order(id: int, name: str):
    with Session(engine) as session:
        new_row = OrderTable(id=id, name=name)

        session.add(new_row)
        session.commit()
        statement = select(OrderTable)
        db_orders = session.exec(statement).all()
        return db_orders


# update order
def update_order(id, name):
    with Session(engine) as session:

        update_order = session.get(OrderTable, id)
        if not update_order:
            return session.exec(select(OrderTable)).all()
        update_order.name = name
        session.add(update_order)
        session.commit()
        statement = select(OrderTable)
        db_orders = session.exec(statement).all()
        return db_orders


# delete order
def delete_order(id: int):
    with Session(engine) as session:
        order_to_delete = session.get(OrderTable, id)
        if order_to_delete:
            session.delete(order_to_delete)
            session.commit()
        statement = select(OrderTable)
        db_orders = session.exec(statement).all()

        return db_orders


# delete many
def delete_all_orders():
    with Session(engine) as session:
        statement = delete(OrderTable)
        session.exec(statement)
        session.commit()
        return []


# rest endpoints
api_router = APIRouter(prefix="/api", tags=["Orders"])


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@api_router.on_event("startup")
def on_startup():
    create_db_and_tables()


@api_router.get("/check")
def health_check():
    return {"status": "healthy", "service": "order-service"}
