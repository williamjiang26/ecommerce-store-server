from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from dotenv import load_dotenv
# 
from fastapi.middleware.cors import CORSMiddleware
from routes import api_router
from schema import schema



app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "http://localhost:19006", "*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
app.include_router(api_router)