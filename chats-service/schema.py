import strawberry
from typing import AsyncGenerator
from models import Message
from routes import message_history, send_message, listen_messages, listen_all_messages

# ==========================================
# Resolvers
# ==========================================

def resolver_message_history(limit: int = 50) -> list[Message]:
    """Helper resolver to convert DB models to Strawberry types."""
    rows = message_history(limit=limit)
    return [
        Message(
            id=r.id,
            sender_type=r.sender_type,
            sender_name=r.sender_name,
            text=r.text,
        )
        for r in rows
    ]



async def resolver_send_message(
    sender_type: str, 
    sender_name: str, 
    text: str,
    room_id: str, # <-- Pass the client/room track ID
    info: strawberry.Info # <-- 1. Inject the Strawberry Info context
) -> Message:
    """Helper resolver to process message creation and map to Strawberry type."""
    
    # 2. Extract background_tasks that we passed into the FastAPI context
    background_tasks = info.context["background_tasks"]
    
 
    payload = await send_message(
        sender_type=sender_type, 
        sender_name=sender_name, 
        text=text,room_id=room_id,
        background_tasks=background_tasks
    )
    
    return Message(
        id=payload["id"],
        sender_type=payload["sender_type"],
        sender_name=payload["sender_name"],room_id=payload["room_id"],
        text=payload["text"],
    )


async def resolver_listen_messages(room_id: str) -> AsyncGenerator[Message, None]:
    """Helper resolver to handle the asynchronous subscription generator stream."""
    async for message in listen_messages(room_id=room_id):
        yield Message(
            id=message.get("id", ""),
            sender_type=message["sender_type"],
            sender_name=message["sender_name"],
            text=message["text"],
            room_id=message["room_id"]
        )

async def resolver_listen_all_messages() -> AsyncGenerator[Message, None]:
    """Helper resolver to handle the global admin subscription stream."""
    async for data in listen_all_messages():
        yield Message(
            id=data.get("id", ""),
            sender_type=data["sender_type"],
            sender_name=data["sender_name"],
            text=data["text"],
            room_id=data["room_id"]
        )
# ==========================================
# GraphQL Schema Types
# ==========================================

@strawberry.type
class Query:
    message_history: list[Message] = strawberry.field(resolver=resolver_message_history)
    @strawberry.field
    def ping(self) -> str:
        return "pong"

@strawberry.type
class Mutation:
    # Strawberry automatically maps the keyword arguments to the resolver
    send_message: Message = strawberry.field(resolver=resolver_send_message)

@strawberry.type
class Subscription:
    listen_messages: AsyncGenerator[Message, None] = strawberry.subscription(
        resolver=resolver_listen_messages
    )
    listen_all_messages: AsyncGenerator[Message, None] = strawberry.subscription(
        resolver=resolver_listen_all_messages
    )
# ==========================================
# Schema Definition
# ==========================================

schema = strawberry.Schema(
    query=Query, 
    mutation=Mutation, 
    subscription=Subscription
)