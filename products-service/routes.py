from fastapi import APIRouter
from sqlmodel import SQLModel, create_engine, Session, select, delete
from models import ProductTable

import os

DATABASE_URL = os.getenv("PRODUCT_DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)
 
# functions
# get product id
def get_product(id: int):
    with Session(engine) as session:
        product = session.get(ProductTable, id)
        return product


# get products
def get_products():
    with Session(engine) as session:
        statement = select(ProductTable)
        db_products = session.exec(statement).all()
        return db_products

# post product
def post_product(name: str, img:str, stock:bool, price:int):
    with Session(engine) as session:
        new_row = ProductTable(name=name, img=img, stock=stock, price=price)
        session.add(new_row)
        session.commit()
        session.refresh(new_row)
        statement = select(ProductTable)
        db_products = session.exec(statement).all()
        return db_products


# update product id
def update_product(id, name):
    with Session(engine) as session:
        update_product = session.get(ProductTable, id)
        if not update_product:
            return session.exec(select(ProductTable)).all()

        update_product.name = name
        session.add(update_product)
        session.commit()
        statement = select(ProductTable)
        db_products = session.exec(statement).all()
        return db_products


# delete product
def delete_product(id: int):
    with Session(engine) as session:
        product_to_delete = session.get(ProductTable, id)
        if product_to_delete:
            session.delete(product_to_delete)
            session.commit()
        statement = select(ProductTable)
        db_products = session.exec(statement).all()
        return db_products


# delete many
def delete_all_products():
    with Session(engine) as session:
        statement = delete(ProductTable)
        session.exec(statement)
        session.commit()
        return []


# rest endpoints
api_router = APIRouter(prefix="/api", tags=["Products"])


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@api_router.on_event("startup")
def on_startup():
    create_db_and_tables()


@api_router.get("/product")
def read_product():
    return get_product()


@api_router.get("/products")
def read_products():
    return get_products()


@api_router.get("/check")
def health_check():
    return {"status": "healthy", "service": "product-service"}
