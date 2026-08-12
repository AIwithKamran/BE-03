import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI
from supabase import create_client, Client

load_dotenv()

URL = os.getenv("PROJECT_URL")
KEY = os.getenv("PUBLIC_KEY")

supabase: Client = create_client(URL, KEY)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server running and connected to Supabase.")
    yield
    
app = FastAPI(lifespan=lifespan)