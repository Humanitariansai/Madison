"""
Authentication and authorization utilities
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models import User
from src.config import load_env

env = load_env()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = env["SECRET_KEY"]
ALGORITHM = env["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES = env["ACCESS_TOKEN_EXPIRE_MINUTES"]

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(token: str, db: Session):
    """Get current authenticated user from token"""
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user

def create_user(username: str, email: str, password: str, db: Session) -> tuple[bool, str, Optional[User]]:
    """Create a new user"""
    # Check if username exists
    if db.query(User).filter(User.username == username).first():
        return False, "Username already exists", None
    
    # Check if email exists
    if db.query(User).filter(User.email == email).first():
        return False, "Email already registered", None
    
    # Create user
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return True, "User created successfully", user

def authenticate_user(username: str, password: str, db: Session) -> tuple[bool, str, Optional[int]]:
    """Authenticate a user by username or email"""
    # Try to find user by username first
    user = db.query(User).filter(User.username == username).first()
    
    # If not found, try to find by email
    if not user:
        user = db.query(User).filter(User.email == username).first()
    
    if not user:
        return False, "Invalid username or password", None
    
    if not verify_password(password, user.password_hash):
        return False, "Invalid username or password", None
    
    return True, "Authentication successful", user.id

def get_user_by_id(user_id: int, db: Session) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()

