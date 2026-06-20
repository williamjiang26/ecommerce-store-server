import os
import asyncio
from sqlmodel import Session, select

from models import Message, MessageTable, engine
from fastapi import APIRouter, Request,BackgroundTasks
from fastapi.responses import StreamingResponse
from pinecone import Pinecone
from openai import AsyncOpenAI
from typing import AsyncGenerator, Set, List, Dict
import uuid
import redis.asyncio as aioredis
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
# Define a constant channel name for the chat room
CHAT_CHANNEL = "chat:global:stream"
CHAT_STREAM_KEY = "chat:global:messages"


def message_history(limit: int = 50) -> list[MessageTable]:
    """
    Fetches recent messages from the database.
    Kept synchronous as per your original implementation.
    """
    with Session(engine) as session:
        statement = (
            select(MessageTable)
            .order_by(MessageTable.created_at.desc())
            .limit(limit)
        )
        return list(reversed(session.exec(statement).all()))


def _save_to_db_background(sender_type: str, sender_name: str, text: str, room_id: str):
    """Background worker task to persist data to SQL database asynchronously."""
    with Session(engine) as session:
        db_msg = MessageTable(
            sender_type=sender_type, sender_name=sender_name, text=text,
            room_id=room_id
        )
        session.add(db_msg)
        session.commit()


async def send_message(sender_type: str, sender_name: str, text: str, room_id: str, background_tasks: BackgroundTasks) -> dict:
    """
    Saves a message to Redis Streams, broadcasts via Pub/Sub, 
    and offloads the SQL write to a background thread.
    """
    payload = {
        "sender_type": sender_type,
        "sender_name": sender_name,
        "text": text,  
        "room_id": room_id
    }
    print(payload)
    # 1. Target the distinct client's stream key
    stream_key = f"chat:room:{room_id}"
    message_id = await redis_client.xadd(stream_key, {"data": json.dumps(payload)}, id="*")
    await redis_client.xtrim(stream_key, maxlen=500, approximate=True)
    payload["id"] = message_id

    # 2. Publish to the distinct client's channel
    pubsub_channel = f"channel:room:{room_id}"
    await redis_client.publish(pubsub_channel, json.dumps(payload))

    # 3. Offload the slow relational DB write to a background task so the API remains lightning fast
    background_tasks.add_task(_save_to_db_background, sender_type, sender_name, text, room_id)

    return payload



async def listen_messages(room_id: str) -> AsyncGenerator[Message, None]:
    """Yields new messages to connected clients via Redis Pub/Sub across any server instance."""
    # Create a unique pubsub context for this connection
    pubsub = redis_client.pubsub()
    pubsub_channel = f"channel:room:{room_id}"
    await pubsub.subscribe(pubsub_channel)

    HEARTBEAT_INTERVAL = 30.0  # Seconds between pings
    idle_time = 0.0
    try:
        while True:
            # listen() blocks asynchronously until a new message is published to the channel
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            # Ignore the initial confirmation subscription message
            if message:
                idle_time = 0.0
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    yield data
            if idle_time >= HEARTBEAT_INTERVAL:
                try:
                    # Actively ping the Redis server to verify connection health
                    await pubsub.ping()
                    
                    # OPTIONAL: Yield a heartbeat token to keep the GraphQL/WebSocket connection alive too
                    # yield {"id": "heartbeat", "sender_type": "system", "text": "ping"}
                except Exception:
                    # If ping fails, the connection is dead; break out to trigger the reconnect
                    print(f"Redis Pub/Sub connection lost for room {room_id}")
                    break
                idle_time = 0.0

            # Yield control back to the event loop for a microsecond
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        # Handles client disconnect cleanly
        pass
    finally:
        # Alwa
        # ys unsubscribe and close the pubsub connection to prevent memory leaks
        await pubsub.unsubscribe(pubsub_channel)        
        await pubsub.close()

async def listen_all_messages():
    """Listens to ALL chat rooms simultaneously using pattern matching."""
    pubsub = redis_client.pubsub()
    # The '*' acts as a wildcard matching any string after channel:room:
    wildcard_pattern = "channel:room:*"
    await pubsub.psubscribe(wildcard_pattern)
    HEARTBEAT_INTERVAL = 30.0  # Seconds between pings
    idle_time = 0.0
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                idle_time = 0.0
                if message["type"] == "pmessage":
                    data = json.loads(message["data"])
                    yield data
            else:
                idle_time += 1.0
                    # 
            if idle_time >= HEARTBEAT_INTERVAL:
                try:
                    # Actively ping the Redis server to verify connection health
                    await pubsub.ping()
                    
                    # OPTIONAL: Yield a heartbeat token to keep the GraphQL/WebSocket connection alive too
                    # yield {"id": "heartbeat", "sender_type": "system", "text": "ping"}
                except Exception:
                    break

                idle_time = 0.0

            # Yield control back to the event loop for a microsecond
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        pass
    finally:
        # Clean up the pattern subscription
        await pubsub.punsubscribe(wildcard_pattern)
        await pubsub.close()

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
async def chat_endpoint(request: Request, background_tasks: BackgroundTasks):

    # 1. Parse the entire incoming chat history array
    payload = await request.json()
    print(payload)
    room_id = payload.get('roomId')
    chat_history: List[Dict[str, str]] = payload.get("messages", [])
    if not room_id or not chat_history:
        return {"error", "Missing roomId or messages history"}, 400

        # 
    last_message = chat_history[-1]
    text = last_message.get("content", "")     
    user_payload = {
        "sender_type": "user",
        "sender_name": "user",
        "text": text,
        "room_id": room_id
    }
    # message to room
    stream_key = f"chat:room:{room_id}"
    message_id = await redis_client.xadd(stream_key, {"data": json.dumps(user_payload)}, id="*")
    await redis_client.xtrim(stream_key, maxlen=500, approximate=True)
    user_payload["id"] = message_id

    # 2. Publish to the distinct client's channel
    pubsub_channel = f"channel:room:{room_id}"
    await redis_client.publish(pubsub_channel, json.dumps(user_payload))
    background_tasks.add_task(_save_to_db_background, "user", "user", text, room_id)
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

    # 6. Append the vector context to the last user message
    last_message_content = text + result_string
    
    # 7. Reconstruct the message payloads for the completion model
    chat_history_without_last = chat_history[:-1]
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

    # 9. Asynchronous generator to stream tokens to the client
    assistant_message_id = f"assistant:{uuid.uuid4()}"
    async def stream_generator():
        full_assistant_text = ""
        try:
            async for chunk in completion:
                # Check for content inside choices safely
                if chunk.choices and chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    full_assistant_text += content_chunk
                    # Create a payload matching what your subscription expects
                    agent_payload = {
                        "id": assistant_message_id,
                        "sender_type": "assistant",
                        "sender_name": "assistant",
                        "text": content_chunk,
                        "room_id": room_id
                    }
                    # put the agent's message with the room to be streamed by the sales rep
                    await redis_client.xadd(stream_key, {"data": json.dumps(agent_payload)}, id="*")
                    await redis_client.xtrim(stream_key, maxlen=500, approximate=True)
                    await redis_client.publish(pubsub_channel, json.dumps(agent_payload))
                    # Yield to the immediate HTTP client (the chat box)
                    yield content_chunk

            background_tasks.add_task(_save_to_db_background, "assistant", "assistant", result_string, room_id)
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
