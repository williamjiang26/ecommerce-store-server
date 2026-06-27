import strawberry
from typing import List, Optional
from models import Customer, AccountInput, Account, Orders, OrdersInput

from routes import (
    get_customer,
    get_customers,
    post_customer,
    update_customer_orders,
    update_customer_information,
    delete_customer,
    delete_all_customers,
)


# resolver
def resolver_customer(id: int) -> Optional[Customer]:
    c = get_customer(id)
    if c:
        return Customer(id=c.id, account_information=Account(id=c.account_information.id,  email=c.account_information.email), 
           orders= [Orders(id=o.id, productId=o.product_id, isPurchased=o.is_purchased) for o in c.orders ], shopping_cart= [ Orders(id=o.id, productId=o.product_id, isPurchased=o.is_purchased) for o in c.shopping_cart ])
    return None



def resolver_customers() -> List[Customer]:
    updated_customers = get_customers()
    return [Customer(id=c.id, account_information=Account(id=c.account_information.id,  email=c.account_information.email), 
           orders= [Orders(id=o.id, productId=o.product_id, isPurchased=o.is_purchased) for o in c.orders ], shopping_cart= [ Orders(id=o.id, productId=o.product_id, isPurchased=o.is_purchased) for o in c.shopping_cart ]) for c in updated_customers]

def resolver_post_customer(account_information: AccountInput ) -> List[Customer]:
    updated_customers = post_customer(account_information)
    return [Customer(id=c.id, account_information=Account(
                id=c.account_information.id, 
                email=c.account_information.email
            ), 
            orders=[], 
            shopping_cart=[]) for c in updated_customers]

def resolver_update_customerOrders(account_information: AccountInput, orders: OrdersInput) -> List[Customer]:
    updated_customers = update_customer_orders(account_information, orders)
    return [Customer(id=c.id, account_information=Account(id=c.account_information.id,  email=c.account_information.email), 
           orders= [Orders(id=o.id, productId=o.product_id, isPurchased=o.is_purchased) for o in c.orders ], shopping_cart= [ Orders(id=o.id, productId=o.product_id, isPurchased=o.is_purchased) for o in c.shopping_cart ]) for c in updated_customers]


def resolver_update_customerInformation(account_information: AccountInput) -> List[Customer]:
    updated_customers = update_customer_information(account_information)
    return [Customer(id=c.id, account_information=Account(id=c.account_information.id,  email=c.account_information.email), 
           orders= [Orders(id=o.id, productId=o.product_id, isPurchased=o.is_purchased) for o in c.orders ], shopping_cart= [ Orders(id=o.id, productId=o.product_id, isPurchased=o.is_purchased) for o in c.shopping_cart ]) for c in updated_customers]
 
# def resolver_delete_customer(id: int) -> List[Customer]:
#     updated_customers = delete_customer(id)
#     return [Customer(id=c.id, account_info=c.account_info, orders=c.orders, shopping_cart=c.shopping_cart) for c in updated_customers]

# def resolver_delete_customers() -> List[Customer]:
#     updated_customers = delete_all_customers()
#     return updated_customers

# graphql functioncalls
@strawberry.type
class Query:
    customer: Customer = strawberry.field(resolver=resolver_customer)
    customers: List[Customer] = strawberry.field(resolver=resolver_customers)




@strawberry.type
class Mutation:
    post_customer: List[Customer] = strawberry.field(resolver=resolver_post_customer)
    update_customer_orders: List[Customer] = strawberry.field(resolver=resolver_update_customerOrders)
    update_customer_information: List[Customer] = strawberry.field(resolver=resolver_update_customerInformation)

    
    # delete_customer: List[Customer] = strawberry.field(
    #     resolver=resolver_delete_customer
    # )
    # delete_customers: List[Customer] = strawberry.field(
    #     resolver=resolver_delete_customers
    # )


schema = strawberry.Schema(query=Query, mutation=Mutation)
