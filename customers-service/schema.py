import strawberry
from typing import List, Optional
from models import Customer

from routes import (
    get_customers,
    get_customer,
    post_customer,
    update_customer,
    delete_customer,
    delete_all_customers,
)


# resolver
def resolver_customer(id: int) -> Optional[Customer]:
    c = get_customer(id)
    if c:
        return Customer(id=c.id, name=c.name)
    return None


def resolver_customers() -> List[Customer]:
    updated_customers = get_customers()
    return [Customer(id=c.id, name=c.name) for c in updated_customers]


def resolver_post_customer(id: int, name: str) -> List[Customer]:
    updated_customers = post_customer(id, name)
    return [Customer(id=c.id, name=c.name) for c in updated_customers]


def resolver_update_customer(id: int, name: str) -> List[Customer]:
    updated_customers = update_customer(id, name)
    return [Customer(id=c.id, name=c.name) for c in updated_customers]


def resolver_delete_customer(id: int) -> List[Customer]:
    updated_customers = delete_customer(id)
    return [Customer(id=c.id, name=c.name) for c in updated_customers]


def resolver_delete_customers() -> List[Customer]:
    updated_customers = delete_all_customers()
    return updated_customers


# graphql functioncalls
@strawberry.type
class Query:
    customer: Customer = strawberry.field(resolver=resolver_customer)
    customers: List[Customer] = strawberry.field(resolver=resolver_customers)


@strawberry.type
class Mutation:
    post_customer: List[Customer] = strawberry.field(resolver=resolver_post_customer)
    update_customer: List[Customer] = strawberry.field(
        resolver=resolver_update_customer
    )
    delete_customer: List[Customer] = strawberry.field(
        resolver=resolver_delete_customer
    )
    delete_customers: List[Customer] = strawberry.field(
        resolver=resolver_delete_customers
    )


schema = strawberry.Schema(query=Query, mutation=Mutation)
