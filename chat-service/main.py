from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from sqlmodel import Session, select
from models import init_db, engine, MessageTable
from schema import schema

app = FastAPI(title="Unified Broadcast Chat Service")


# Initialize PostgreSQL Database schema on application startup
@app.on_event("startup")
def on_startup():
    init_db()


# Security CORS Configuration Layer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# STANDARD HTTP REST ROUTES
# ---------------------------------------------------------------------


@app.get("/health", tags=["Monitoring"])
def health_check():
    """Standard HTTP load-balancer health ping target"""
    return {"status": "healthy", "transport": "in-memory-queues"}


@app.get("/api/messages", response_model=list[dict], tags=["Chat Data"])
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


app.include_router(GraphQLRouter(schema), prefix="/graphql")
