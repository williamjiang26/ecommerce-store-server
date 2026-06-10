from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from models import init_db
from schema import schema
from routes import api_router
app = FastAPI(title="Customer Service Chat")


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

 
app.include_router(GraphQLRouter(schema), prefix="/graphql")
app.include_router(api_router)