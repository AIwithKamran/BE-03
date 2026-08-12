import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from pydantic import BaseModel

class AuthRequest(BaseModel):
    email: str = None
    password: str = None
    
load_dotenv()

URL = os.getenv("PROJECT_URL")
KEY = os.getenv("PUBLIC_KEY")

supabase: Client = create_client(URL, KEY)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server running and connected to Supabase.")
    yield
    
app = FastAPI(lifespan=lifespan)


@app.post("/auth/signup")
async def signup(body: AuthRequest):
    if not body.email or not body.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        result = supabase.auth.sign_up(
            {
                'email': body.email,
                'password': body.password
            }
        )
        if result.user is None:
            raise HTTPException(status_code=400, detail="Signup failed")

        return JSONResponse(status_code=201, content={'user': result.user.model_dump(mode='json')})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/auth/login')
async def login(body: AuthRequest):
    if not body.email or not body.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        result = supabase.auth.sign_in_with_password(
            {
                'email': body.email,
                'password': body.password
            }
        )
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid login credentials')

    return JSONResponse(
        status_code=200,
        content={
            'access_token': result.session.access_token,
            'refresh_token': result.session.refresh_token
        }
    )
    
@app.get('/public/info')
async def public_info():
    return {"message": "Welcome Stranger! This info is public."}

@app.get("/protected/profile")
async def protected_profile(request : Request):
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"error" : "Access Token required"})
    
    token = auth_header.split(" ")[1]
    
    try:
        user_response = supabase.auth.get_user(token)
    except:
        return JSONResponse(status_code=401, content={"message":"Invalid Key"})
    
    if user_response is None or user_response.user is None:
        return JSONResponse(status_code=401, content={"error": "Invalid or expired token"})
    
    user = user_response.user
    
    return JSONResponse(
        status_code=200,
        content={
            "id": user.id,
            "email":user.email,
            'created_at': str(user.created_at)
        }
    )
