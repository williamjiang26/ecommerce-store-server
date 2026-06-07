import strawberry
from typing import List, Optional
from models import Order

from routes import get_orders, get_order, post_order, update_order, delete_order, delete_all_orders


# resolver
def resolver_order(id:int) -> Optional[Order]:
    o = get_order(id)
    if o:
        return Order(id=o.id, name=o.name)
    return None



def resolver_orders() -> List[Order]:
    updated_orders = get_orders()
    return [
        Order(id=o.id, name=o.name) 
        for o in updated_orders
    ]

def resolver_post_order(id: int, name: str) -> List[Order]:
    updated_orders = post_order(id, name)
    return [
        Order(id=o.id, name=o.name) 
        for o in updated_orders
    ]

def resolver_update_order(id: int, name: str) -> List[Order]:
    updated_orders = update_order(id, name)
    return [
        Order(id=o.id, name=o.name) 
        for o in updated_orders
    ]

def resolver_delete_order(id: int) -> List[Order]:
    updated_orders = delete_order(id)
    return [
        Order(id=o.id, name=o.name) 
        for o in updated_orders
    ]

def resolver_delete_orders() -> List[Order]:
    updated_orders = delete_all_orders()
    return updated_orders
# graphql functioncalls
@strawberry.type
class Query:
    order: Order = strawberry.field(resolver=resolver_order)
    orders: List[Order] = strawberry.field(resolver=resolver_orders)


@strawberry.type
class Mutation:
    post_order: List[Order] = strawberry.field(resolver=resolver_post_order)
    update_order: List[Order] = strawberry.field(resolver=resolver_update_order)
    delete_order: List[Order] = strawberry.field(resolver=resolver_delete_order)
    delete_orders: List[Order] = strawberry.field(resolver=resolver_delete_orders)
schema = strawberry.Schema(query=Query, mutation=Mutation)