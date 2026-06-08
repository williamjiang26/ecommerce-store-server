from fastapi import APIRouter
from sqlmodel import SQLModel, Field, create_engine,Session, select, delete
import os

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL =  os.getenv("CUSTOMER_DATABASE_URL")
# Create the async engine
engine = create_engine(DATABASE_URL, echo=True)
# SQLModel DB Table Definition (Acts as both SQLAlchemy table and Pydantic validation)
class CustomerTable(SQLModel, table=True):
    __tablename__ = "customers"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)



# functions
# get customer
def get_customer(id:int):
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
def post_customer(id: int, name: str):
    with Session(engine) as session:
        # 2. Create an instance of your database table row model
        new_row = CustomerTable(id=id, name=name)
        
        # 3. Add and commit the new record to PostgreSQL
        session.add(new_row)
        session.commit()
        
        # 4. Fetch the entire updated list of rows from the database to return
        statement = select(CustomerTable)
        db_customers = session.exec(statement).all()
        
        return db_customers
# update customer
def update_customer(id, name):
      with Session(engine) as session:
            update_customer = session.get(CustomerTable,id)
            if not update_customer:
                return session.exec(select(CustomerTable)).all()

            update_customer.name = name
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
