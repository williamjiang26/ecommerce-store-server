import strawberry
from typing import AsyncGenerator
from models import Message
import routes

# ==========================================
# Resolvers
# ==========================================

def resolver_message_history(limit: int = 50) -> list[Message]:
    """Helper resolver to convert DB models to Strawberry types."""
    rows = routes.message_history(limit=limit)
    return [
        Message(
            id=r.id,
            sender_type=r.sender_type,
            sender_name=r.sender_name,
            text=r.text,
        )
        for r in rows
    ]


def resolver_send_message(sender_type: str, sender_name: str, text: str) -> Message:
    """Helper resolver to process message creation and map to Strawberry type."""
    db_msg = routes.send_message(
        sender_type=sender_type, sender_name=sender_name, text=text
    )
    return Message(
        id=db_msg.id,
        sender_type=db_msg.sender_type,
        sender_name=db_msg.sender_name,
        text=db_msg.text,
    )


async def resolver_listen_messages() -> AsyncGenerator[Message, None]:
    """Helper resolver to handle the asynchronous subscription generator stream."""
    async for message in routes.listen_messages():
        yield message


# ==========================================
# GraphQL Schema Types
# ==========================================

@strawberry.type
class Query:
    message_history: list[Message] = strawberry.field(resolver=resolver_message_history)


@strawberry.type
class Mutation:
    send_message: Message = strawberry.field(resolver=resolver_send_message)


@strawberry.type
class Subscription:
    listen_messages: AsyncGenerator[Message, None] = strawberry.subscription(
        resolver=resolver_listen_messages
    )

# ==========================================
# Schema Definition
# ==========================================

schema = strawberry.Schema(
    query=Query, 
    mutation=Mutation, 
    subscription=Subscription
)