from fastapi import APIRouter, HTTPException, status, Request
from sqlmodel import SQLModel, Session, select, delete
from models import EmployeeTable, engine, Employee

from typing import Optional
# functions
# get employee
def get_employee(cognitoId: str):
    with Session(engine) as session:
        employee = session.get(EmployeeTable, id)
        return employee


# get employee
def get_employees():
    with Session(engine) as session:
        statement = select(EmployeeTable)
        db_employee = session.exec(statement).all()
        return db_employee


# post employee - create new user
def post_employee(
    name: str, 
    cognitoId: str, 
    userRole: str, 
    storeId: Optional[int] = None, 
    email: str = "", 
    phoneNumber: str = ""
) -> EmployeeTable:
    with Session(engine) as session:
        # Create a new row instance mapping frontend payload names to DB columns
        new_row = EmployeeTable(
            name=name,
            cognitoId=cognitoId,
            role=userRole.lower(),  # DB column name is 'role'
            storeId=storeId,        # DB column name is 'storeId'
            email=email,
            phoneNumber=phoneNumber
        )
        
        session.add(new_row)
        session.commit()
        session.refresh(new_row)  # Populates the auto-increment ID from PostgreSQL
        return new_row
# update employee
def update_employee(id, name):
    with Session(engine) as session:
        update_employee = session.get(EmployeeTable, id)
        if not update_employee:
            return session.exec(select(EmployeeTable)).all()

        update_employee.name = name
        session.add(update_employee)
        session.commit()
        statement = select(EmployeeTable)
        db_employee = session.exec(statement).all()
        return db_employee


# delete employee
def delete_employee(id: int):
    with Session(engine) as session:
        employee_to_delete = session.get(EmployeeTable, id)
        if employee_to_delete:
            session.delete(employee_to_delete)
            session.commit()
        statement = select(EmployeeTable)
        db_employee = session.exec(statement).all()
        return db_employee


# delete many
def delete_all_employees():
    with Session(engine) as session:
        statement = delete(EmployeeTable)
        session.exec(statement)
        session.commit()
        return []


# rest endpoints
api_router = APIRouter(prefix="/api", tags=["employee"])


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@api_router.post("/manager") 
async def create_manager_account(request: Request):
    body = await request.json()
    print(body)
    # return post_employee(
    #     name=payload.name,
    #     cognitoId=payload.cognitoId, # Captures the user.userId sent in the body
    #     userRole="manager"
    # )

@api_router.post("/sales")
def create_sales_account(payload: Employee):
    return post_employee(
        name=payload.name,
        cognitoId=payload.cognitoId,
        userRole="sales",
        storeId=payload.storeId
    ) 

@api_router.on_event("startup")
def on_startup():
    create_db_and_tables()


@api_router.get("/check")
def health_check():
    return {"status": "healthy", "service": "employee-service"}
