from typing import List, Optional
import strawberry
from models import Essay

from routes import (
    get_essay,
    get_essays,
    post_essay,
    update_essay,
    delete_essay,
    delete_all_essays,
)

# =====================================================================
# GRAPHQL RESOLVERS
# =====================================================================

def resolver_essay(title: str) -> Optional[Essay]:
    e = get_essay(title)
    if e:
        return Essay(id=e.id, date=e.date, title=e.title, content=e.content)
    return None


def resolver_essays() -> List[Essay]:
    updated_essays = get_essays()
    return [
        Essay(id=e.id, date=e.date, title=e.title, content=e.content) 
        for e in updated_essays
    ]


def resolver_post_essay(date: str, title: str, content: Optional[str] = None) -> List[Essay]:
    updated_essays = post_essay(date, title, content)
    return [
        Essay(id=e.id, date=e.date, title=e.title, content=e.content) 
        for e in updated_essays
    ]


def resolver_update_essay(
    id: int, 
    date: str, 
    title: str, 
    content: Optional[str] = None
) -> List[Essay]:
    updated_essays = update_essay(id, date, title, content)
    return [
        Essay(id=e.id, date=e.date, title=e.title, content=e.content) 
        for e in updated_essays
    ]


def resolver_delete_essay(id: int) -> List[Essay]:
    updated_essays = delete_essay(id)
    return [
        Essay(id=e.id, date=e.date, title=e.title, content=e.content) 
        for e in updated_essays
    ]


def resolver_delete_essays() -> List[Essay]:
    return delete_all_essays()





@strawberry.type
class Query:
    essay: Optional[Essay] = strawberry.field(resolver=resolver_essay)
    essays: List[Essay] = strawberry.field(resolver=resolver_essays)


@strawberry.type
class Mutation:
    post_essay: List[Essay] = strawberry.field(resolver=resolver_post_essay)
    update_essay: List[Essay] = strawberry.field(resolver=resolver_update_essay)
    delete_essay: List[Essay] = strawberry.field(resolver=resolver_delete_essay)
    delete_essays: List[Essay] = strawberry.field(resolver=resolver_delete_essays) 

schema = strawberry.Schema(query=Query, mutation=Mutation)