from fastapi import FastAPI , BackgroundTasks
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
async def get_graphql_context(background_tasks: BackgroundTasks):
    return {
        "background_tasks": background_tasks,
    }


# 2. Pass the context getter into the GraphQLRouter.
# This router automatically handles standard HTTP POST requests (for Mutations/Queries)
graphql_router = GraphQLRouter(schema, context_getter=get_graphql_context)
 
app.include_router(graphql_router, prefix="/graphql")
app.include_router(api_router)