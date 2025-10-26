from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Dict, Optional
import hashlib
import secrets
import json
from pathlib import Path

router = APIRouter()

DB_DIR = Path(__file__).parent.parent.parent / "data"
USERS_DB_FILE = DB_DIR / "users.json"
SESSIONS_DB_FILE = DB_DIR / "sessions.json"

DB_DIR.mkdir(exist_ok=True)

def load_users() -> Dict[str, Dict]:
    if USERS_DB_FILE.exists():
        with open(USERS_DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users: Dict[str, Dict]):
    with open(USERS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_sessions() -> Dict[str, str]:
    if SESSIONS_DB_FILE.exists():
        with open(SESSIONS_DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_sessions(sessions: Dict[str, str]):
    with open(SESSIONS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

users_db: Dict[str, Dict] = load_users()
sessions: Dict[str, str] = load_sessions()

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    email: str
    token: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

@router.post("/register", response_model=UserResponse)
async def register(user: UserRegister):
    if user.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    for existing_user in users_db.values():
        if existing_user["email"] == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    
    hashed_password = hash_password(user.password)
    
    users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password
    }
    save_users(users_db)
    
    token = generate_token()
    sessions[token] = user.username
    save_sessions(sessions)
    
    return UserResponse(
        username=user.username,
        email=user.email,
        token=token
    )

@router.post("/login", response_model=UserResponse)
async def login(credentials: UserLogin):
    user = users_db.get(credentials.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    hashed_password = hash_password(credentials.password)
    
    if user["password"] != hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    token = generate_token()
    sessions[token] = credentials.username
    save_sessions(sessions)
    
    return UserResponse(
        username=user["username"],
        email=user["email"],
        token=token
    )

@router.post("/logout")
async def logout(token: str):
    if token in sessions:
        del sessions[token]
        save_sessions(sessions)
        return {"message": "登出成功"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的令牌"
    )

@router.get("/me")
async def get_current_user(token: str):
    username = sessions.get(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授权"
        )
    
    user = users_db.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {
        "username": user["username"],
        "email": user["email"]
    }
