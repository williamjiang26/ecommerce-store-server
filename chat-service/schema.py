from routes import send_message, listen_messages, check
from models import Message
import strawberry

from typing import AsyncGenerator 
#  resolver
def resolver_message(sender: str, text: str) -> Message:
    m = send_message(sender=sender, text=text)
    # FIXED: Unpack the dictionary using ** so it populates Message correctly
    return Message(**m)

async def resolver_messages() -> AsyncGenerator[Message, None]:
    async for m in listen_messages():
        yield Message(**m)


# graphql functioncalls
@strawberry.type
class Query:
    @strawberry.field
    def status(self) -> str: 
        return check()


@strawberry.type
class Mutation:
    @strawberry.field
    def message(sender: str, text: str) -> Message:
        return resolver_message(sender, text)

@strawberry.type
class Subscription:
    messages: AsyncGenerator[Message, None] = strawberry.field(resolver=resolver_messages)



schema = strawberry.Schema(query=Query,mutation=Mutation, subscription=Subscription)