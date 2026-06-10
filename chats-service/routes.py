import os
import asyncio
from sqlmodel import Session, select

from models import Message, MessageTable, engine
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pinecone import Pinecone
from openai import AsyncOpenAI
from typing import AsyncGenerator, Set, List, Dict
import uuid
# Global memory set to track active subscription queues
ACTIVE_LISTENERS: Set[asyncio.Queue] = set()


def message_history(limit: int = 50) -> list[MessageTable]:
    """Fetches recent messages from the database."""
    with Session(engine) as session:
        statement = (
            select(MessageTable)
            .order_by(MessageTable.created_at.desc())
            .limit(limit)
        )
        # Reverse to return them in chronological order
        return list(reversed(session.exec(statement).all()))


def send_message(sender_type: str, sender_name: str, text: str) -> MessageTable:
    """Saves a message to the database and broadcasts it to active listeners."""
    with Session(engine) as session:
        db_msg = MessageTable(
            sender_type=sender_type, sender_name=sender_name, text=text
        )
        session.add(db_msg)
        session.commit()
        session.refresh(db_msg)

    payload = {
        "id": db_msg.id,
        "sender_type": db_msg.sender_type,
        "sender_name": db_msg.sender_name,
        "text": db_msg.text,
    }
    
    # Broadcast to all active GraphQL subscription streams
    for queue in ACTIVE_LISTENERS:
        queue.put_nowait(payload)

    return db_msg


async def listen_messages() -> AsyncGenerator[Message, None]:
    """Yields new messages to connected GraphQL subscription clients."""
    queue = asyncio.Queue()
    ACTIVE_LISTENERS.add(queue)

    try:
        while True:
            data = await queue.get()
            yield Message(
                id=data["id"],
                sender_type=data["sender_type"],
                sender_name=data["sender_name"],
                text=data["text"],
            )
    finally:
        ACTIVE_LISTENERS.discard(queue)

api_router = APIRouter(prefix="/api", tags=["Chats"])

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("cxsupport")


SYSTEM_PROMPT = """
You are an intelligent assistant specialized in helping customers find out about their order details. 
Customers will ask you about their order details, make sure to ask for their invoice number and name. If you dont have an invoice number and a name do not reveal any order details. 
Once you have confirmed these two pieces of information, go ahead search for their order in the database and 
respond with the products in their order and order total. If and only if the customer asks about servicing their order and the order is more than 3 years old, inform them it is out of our warranty and would incur a cost but we would be happy to help them schedule a service date.
Use Retrieval-Augmented Generation (RAG) to pull in relevant data from multiple sources, 
combining it with your knowledge to generate accurate, insightful, and assistance.
Ensure your responses are concise, informative and hospitable.
Always prioritize assistance and support and confirm the invoice number and name before giving order details
"""

openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

@api_router.post("/chat")
async def chat_endpoint(request: Request):

    # 1. Parse the entire incoming chat history array
    data: List[Dict[str, str]] = await request.json()
    
    # 2. Get the last user message text
    last_message = data[-1]
    text = last_message.get("content", "")

    user_payload = {
        "id": str(uuid.uuid4()),  # Unique ID for the user's message block
        "sender_type": "user",
        "sender_name": "user",
        "text": text,
    }
    for queue in ACTIVE_LISTENERS:
        queue.put_nowait(user_payload)
    # 3. Generate the vector embedding using OpenRouter
    embedding_response = await openrouter_client.embeddings.create(
        model="nvidia/llama-nemotron-embed-vl-1b-v2:free",
        input=text,
        encoding_format="float"
    )
    vector = embedding_response.data[0].embedding
    
    # 4. Query Pinecone for the top matching document
    results = index.query(
        namespace="ns1",
        top_k=1,
        include_metadata=True,
        vector=vector
    )
    
    # 5. Build the context string from matched data
    result_string = "Returned results:"
    for match in results.get("matches", []):
        print(f"🚀 ~ POST ~ match: {match}")
        metadata = match.get("metadata", {})
        result_string += f"""\n
        InvoiceNo: {match.get('id')}
        Date Ordered: {metadata.get('date Ordered')}
        OrderStatus: {metadata.get('status')}
        Customer Name: {metadata.get('customerName')}
        Order Details: {metadata.get('order')}
        Order Total: {metadata.get('totalPrice')}
        \n\n
        """
    print(f"🚀 ~ POST ~ resultString: {result_string}")
    
    # 6. Append the vector context to the last user message
    last_message_content = text + result_string
    
    # 7. Reconstruct the message payloads for the completion model
    chat_history_without_last = data[:-1]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    # Add back the conversation history
    messages.extend(chat_history_without_last)
    # Add the final augmented user message
    messages.append({"role": "user", "content": last_message_content})
    
    # 8. Request a streaming completion from OpenRouter
    completion = await openrouter_client.chat.completions.create(
        model="nvidia/nemotron-3-nano-30b-a3b:free",
        messages=messages,
        stream=True
    )
    agent_message_id = str(uuid.uuid4())
    # 9. Asynchronous generator to stream tokens to the client
    async def stream_generator():
        try:
            async for chunk in completion:
                # Check for content inside choices safely
                if chunk.choices and chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    # Create a payload matching what your subscription expects
                    payload = {
                        "id": agent_message_id,
                        "sender_type": "assistant",
                        "sender_name": "assistant",
                        "text": content_chunk,
                    }
                    for queue in ACTIVE_LISTENERS:
                        queue.put_nowait(payload)

                    # Yield to the immediate HTTP client (the chat box)
                    yield content_chunk

        except Exception as e:
            # Handle potential connection drops/errors
            print(f"Streaming Error: {e}")
            yield f"Error: {str(e)}"

    
    return StreamingResponse(stream_generator(), media_type="text/plain")        

@api_router.get("/health", tags=["Monitoring"])
def health_check():
    """Standard HTTP load-balancer health ping target"""
    return {"status": "healthy", "transport": "in-memory-queues"}




@api_router.get("/messages", response_model=list[dict], tags=["Chat Data"])
def get_all_messages_rest(limit: int = 100):
    """
    Standard REST endpoint fallback.
    Allows dashboards or analytics engines to pull historical messages via standard HTTP GET.
    """
    with Session(engine) as session:
        statement = (
            select(MessageTable).order_by(MessageTable.created_at.desc()).limit(limit)
        )
        results = session.exec(statement).all()

        # Format results into plain JSON dictionaries for standard REST consumption
        return [
            {
                "id": msg.id,
                "sender_type": msg.sender_type,
                "sender_name": msg.sender_name,
                "text": msg.text,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in reversed(results)
        ]
