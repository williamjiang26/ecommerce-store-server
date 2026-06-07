import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
# from kafka_io import active_websocket_queues, get_kafka_producer
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")


client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENROUTER_API_KEY,
)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("cxsupport")
systemPrompt = """
    You are an intelligent assistant specialized in helping customers find out about their order details. 
    Customers will ask you about their order details, make sure to ask for their invoice number and name. If you dont have an invoice number and a name do not reveal any order details. 
    Once you have confirmed these two pieces of information, go ahead search for their order in the database and 
    respond with the products in their order and order total. If and only if the customer asks about servicing their order and the order is more than 3 years old, inform them it is out of our warranty and would incur a cost but we would be happy to help them schedule a service date.
    Use Retrieval-Augmented Generation (RAG) to pull in relevant data from multiple sources, 
    combining it with your knowledge to generate accurate, insightful, and assistance.
    Ensure your responses are concise, informative and hospitable.
    Always prioritize assistance and support and confirm the invoice number and name before giving order details
    """

api_router = APIRouter(prefix="/api", tags=["Chats"])


_message_queues = []

def send_message(sender: str, text: str):
    new_msg = {"sender": sender, "text": text}   
    for q in _message_queues:
        q.put_nowait(new_msg)
    print(new_msg)
    return new_msg


  
# used by both customer and admin clients  
async def listen_messages():
    # Create a unique queue for this specific connected client
    queue = asyncio.Queue()
    _message_queues.append(queue)
    try:
        while True:
            # Wait until a new message arrives and yield it to the client
            message = await queue.get()
            yield message
    finally:
        # Clean up when the client disconnects
        _message_queues.remove(queue)

                       




@api_router.get("/")
def ping(self) -> str: return "pong"
@api_router.post("/api/chat/stream")
def chat_stream(request: dict):
    message = request["messages"]
    lastMessage = message[-1]
    embedding = client.embeddings.create(
        model="nvidia/llama-nemotron-embed-vl-1b-v2:free",
        input=[lastMessage["content"]],
        encoding_format="float"
    ).data[0].embedding
    results = index.query(
        namespace="ns1",
        vector=embedding, 
        top_k=1,
        include_metadata=True
        )
    resultString = "Returned results:"
    for match in results.matches:
        resultString += f"""InvoiceNo: ${match.id}Date Ordered: ${match.metadata}OrderStatus: ${match.metadata['status']}
        Customer Name: ${match.metadata['customerName']}
        Order Details: ${match.metadata['order']}
        Order Total: ${match.metadata['totalPrice']}"""
    lastMessageContent = lastMessage["content"] + resultString
    lastDataWithoutLastMessage = message[: len(message) - 1]
    lastDataWithoutLastMessage = [{"role": message["role"], "content": message["content"]} for message in lastDataWithoutLastMessage]
    response = client.chat.completions.create(
        model="nvidia/nemotron-3-nano-30b-a3b:free",
        messages=[
            { "role": "system", "content": systemPrompt },
            *lastDataWithoutLastMessage,
            { "role": "user", "content": lastMessageContent },
        ],
        stream=True,
        extra_body={"reasoning": {"enabled": True}},
    )

    def generate():
        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            if content:
                yield content
        return StreamingResponse(generate(), media_type="text/plain")

def check() -> dict:
    return {"status": "ok"}