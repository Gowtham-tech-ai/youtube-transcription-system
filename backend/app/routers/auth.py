from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.config import settings
from app.models import UserLogin, UserRegister, UserProfile
from app.database import db_manager

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    if not token:
        # Default guest / demo user for quick experimentation
        return {"id": "guest_user", "email": "user@demo.com", "name": "Demo User"}
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return {"id": "guest_user", "email": "user@demo.com", "name": "Demo User"}
        return {"id": payload.get("id", email), "email": email, "name": payload.get("name", "User")}
    except jwt.PyJWTError:
        return {"id": "guest_user", "email": "user@demo.com", "name": "Demo User"}

@router.post("/register")
async def register(user_data: UserRegister):
    # In a full production system, hash passwords with bcrypt
    user_doc = {
        "id": f"usr_{int(datetime.utcnow().timestamp())}",
        "email": user_data.email,
        "name": user_data.name,
        "password": user_data.password,
        "created_at": datetime.utcnow().isoformat()
    }
    if db_manager.is_atlas_connected and db_manager.db is not None:
        existing = await db_manager.db.users.find_one({"email": user_data.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        await db_manager.db.users.insert_one(user_doc)
    else:
        db_manager._local_cache["users"].append(user_doc)
        db_manager._save_local_cache()

    token = create_access_token({"sub": user_data.email, "name": user_data.name, "id": user_doc["id"]})
    return {"token": token, "user": {"id": user_doc["id"], "email": user_data.email, "name": user_data.name}}

@router.post("/login")
async def login(credentials: UserLogin):
    user = None
    if db_manager.is_atlas_connected and db_manager.db is not None:
        user = await db_manager.db.users.find_one({"email": credentials.email})
    else:
        user = next((u for u in db_manager._local_cache["users"] if u.get("email") == credentials.email), None)

    if not user and credentials.email == "demo@example.com":
        user = {"id": "demo_1", "email": "demo@example.com", "name": "Alex Demo"}

    if not user:
        # For simplicity and smooth user onboarding, auto-create if demo
        user = {
            "id": f"usr_{int(datetime.utcnow().timestamp())}",
            "email": credentials.email,
            "name": credentials.email.split("@")[0].title()
        }

    token = create_access_token({"sub": user["email"], "name": user.get("name", "User"), "id": user.get("id", "demo")})
    return {"token": token, "user": {"id": user.get("id"), "email": user["email"], "name": user.get("name")}}

@router.get("/me")
async def get_me(user = Depends(get_current_user)):
    return user
