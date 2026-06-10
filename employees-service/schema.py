import strawberry
from typing import List, Optional
from models import Employee

from routes import (
    get_employee,
    get_employees,
    post_employee,
    update_employee,
    delete_employee,
    delete_all_employees,
)


# resolver
def resolver_employee(cognitoId: str) -> Optional[Employee]:
    c = get_employee(cognitoId)
    # 2. If an employee is found, explicitly map the fields to the GraphQL Type
    if c:
        return Employee(
            id=c.id,
            name=c.name,
            cognitoId=c.cognitoId,
            userRole=c.role,  # Explicitly map database 'role' to GraphQL 'userRole'
            storeId=c.storeId,
            email=c.email,
            phoneNumber=c.phoneNumber,
            img=c.img,
        )

    # 3. Explicitly return None if they don't exist in your DB yet (triggers your frontend 404 block)
    return None


def resolver_employees() -> List[Employee]:
    updated_employees = get_employees()
    return [Employee(**c) for c in updated_employees]


def resolver_post_employee(
    id: int,
    name: str,
    cognitoId: str,
    userRole: str,
    storeId: Optional[int] = None,
    email: str = "",
    phoneNumber: str = "",
) -> List[Employee]:
    new_employee = post_employee(name, cognitoId, userRole, storeId)
    return Employee(
        id=new_employee.id,
        name=new_employee.name,
        cognitoId=new_employee.cognitoId,
        userRole=new_employee.role,
        storeId=new_employee.storeId,
    )


def resolver_update_employee(id: int, name: str) -> List[Employee]:
    updated_employees = update_employee(id, name)
    return [Employee(id=c.id, name=c.name) for c in updated_employees]


def resolver_delete_employee(id: int) -> List[Employee]:
    updated_employees = delete_employee(id)
    return [Employee(id=c.id, name=c.name) for c in updated_employees]


def resolver_delete_employees() -> List[Employee]:
    updated_employees = delete_all_employees()
    return updated_employees


# graphql functioncalls
@strawberry.type
class Query:
    employee: Employee = strawberry.field(resolver=resolver_employee)
    employees: List[Employee] = strawberry.field(resolver=resolver_employees)


@strawberry.type
class Mutation:
    post_employee: Employee = strawberry.field(resolver=resolver_post_employee)
    update_employee: List[Employee] = strawberry.field(
        resolver=resolver_update_employee
    )
    delete_employee: List[Employee] = strawberry.field(
        resolver=resolver_delete_employee
    )
    delete_employees: List[Employee] = strawberry.field(
        resolver=resolver_delete_employees
    )


schema = strawberry.Schema(query=Query, mutation=Mutation)
