import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, Response
from supabase import create_client, Client
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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
security_scheme = HTTPBearer(auto_error=False)

async def get_current_user(request: Request, 
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
    ):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Access token required")
    
    token = credentials.credentials
    
    try:
        user_response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if user_response is None or user_response.user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {'user': user_response.user, "token": token}

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
async def protected_profile(current=Depends(get_current_user)):
    user = current['user']
    return JSONResponse(
        status_code=200,
        content={
            "id": user.id,
            "email":user.email,
            'created_at': str(user.created_at)
        }
    )


@app.get("/protected/dashboard")
async def protected_dashboard(current=Depends(get_current_user)):
    user = current['user']
    return {'message': f'Welcome to your dashboard, {user.email}'}


@app.post("/auth/logout")
async def logout(current=Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return Response(status_code=204)