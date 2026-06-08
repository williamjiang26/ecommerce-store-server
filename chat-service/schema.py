import asyncio
import strawberry
from typing import AsyncGenerator, Set
from sqlmodel import Session, select
from models import engine, MessageTable

ACTIVE_LISTENERS: Set[asyncio.Queue] = set()

@strawberry.type
class Message:
    id: int
    sender_type: str
    sender_name: str
    text: str

@strawberry.type
class Query:
    @strawberry.field
    def message_history(self, limit: int = 50) -> list[Message]:
        with Session(engine) as session:
            statement = select(MessageTable).order_by(MessageTable.created_at.desc()).limit(limit)
            rows = list(reversed(session.exec(statement).all()))
            return [Message(id=r.id, sender_type=r.sender_type, sender_name=r.sender_name, text=r.text) for r in rows]

@strawberry.type
class Mutation:
    @strawberry.field
    def send_message(self, sender_type: str, sender_name: str, text: str) -> Message:
        with Session(engine) as session:
            db_msg = MessageTable(sender_type=sender_type, sender_name=sender_name, text=text)
            session.add(db_msg)
            session.commit()
            session.refresh(db_msg)
        
        payload = {
            "id": db_msg.id, 
            "sender_type": db_msg.sender_type,
            "sender_name": db_msg.sender_name, 
            "text": db_msg.text
        }
        for queue in ACTIVE_LISTENERS:
            queue.put_nowait(payload)
            
        return Message(id=db_msg.id, sender_type=db_msg.sender_type, sender_name=db_msg.sender_name, text=db_msg.text)

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def listen_messages(self) -> AsyncGenerator[Message, None]:
        queue = asyncio.Queue()
        
        # 3. Add the active connection queue to the plain global set
        ACTIVE_LISTENERS.add(queue)
        
        try:
            while True:
                data = await queue.get()
                yield Message(
                    id=data["id"], 
                    sender_type=data["sender_type"], 
                    sender_name=data["sender_name"], 
                    text=data["text"]
                )
        finally:
            # 4. Safely discard the queue resource on connection disconnect
            ACTIVE_LISTENERS.discard(queue)

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)