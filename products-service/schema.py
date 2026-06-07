import strawberry
from typing import List, Optional
from models import Product

from routes import get_products, get_product, post_product, update_product, delete_product, delete_all_products


# resolver
def resolver_product(id:int) -> Optional[Product]:
    p = get_product(id)
    if p:
        return Product(id=p.id, name=p.name)
    return None



def resolver_products() -> List[Product]:
    updated_products = get_products()
    return [
        Product(id=p.id, name=p.name) 
        for p in updated_products
    ]

def resolver_post_product(id: int, name: str) -> List[Product]:
    updated_products = post_product(id, name)
    return [
        Product(id=p.id, name=p.name) 
        for p in updated_products
    ]

def resolver_update_product(id: int, name: str) -> List[Product]:
    updated_products = update_product(id, name)
    return [
        Product(id=p.id, name=p.name) 
        for p in updated_products
    ]

def resolver_delete_product(id: int) -> List[Product]:
    updated_products = delete_product(id)
    return [
        Product(id=p.id, name=p.name) 
        for p in updated_products
    ]

def resolver_delete_products() -> List[Product]:
    updated_products = delete_all_products()
    return updated_products
# graphql functioncalls
@strawberry.type
class Query:
    product: Product = strawberry.field(resolver=resolver_product)
    products: List[Product] = strawberry.field(resolver=resolver_products)

@strawberry.type
class Mutation:
    post_product: List[Product] = strawberry.field(resolver=resolver_post_product)
    update_product: List[Product] = strawberry.field(resolver=resolver_update_product)
    delete_product: List[Product] = strawberry.field(resolver=resolver_delete_product)
    delete_products: List[Product] = strawberry.field(resolver=resolver_delete_products)
schema = strawberry.Schema(query=Query, mutation=Mutation)