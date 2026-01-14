"""
auth_service.py - JWT 身份驗證服務
V10.38: 新增用戶認證和授權功能

功能：
- 密碼雜湊與驗證
- JWT Token 生成與驗證
- 用戶註冊與登入
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db, User

# 密碼雜湊設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 設定
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# JWT 設定（從環境變數讀取）
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "stockbuddy-secret-key-please-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 預設 24 小時


# ===== Pydantic 模型 =====

class TokenData(BaseModel):
    """Token 資料模型"""
    username: Optional[str] = None
    user_id: Optional[int] = None


class Token(BaseModel):
    """Token 回應模型"""
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    """用戶註冊模型"""
    username: str
    password: str
    email: Optional[str] = None


class UserLogin(BaseModel):
    """用戶登入模型"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用戶回應模型"""
    id: int
    username: str
    email: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 密碼處理函數 =====

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """密碼雜湊"""
    return pwd_context.hash(password)


# ===== JWT Token 函數 =====

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """建立存取 Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """解碼 Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None:
            return None
        return TokenData(username=username, user_id=user_id)
    except JWTError:
        return None


# ===== 用戶操作函數 =====

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """依用戶名稱取得用戶"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """依用戶 ID 取得用戶"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user: UserCreate) -> User:
    """建立新用戶"""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """驗證用戶登入"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ===== 依賴注入函數 =====

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """取得目前登入的用戶（可選）"""
    if not token:
        return None

    token_data = decode_token(token)
    if not token_data or not token_data.user_id:
        return None

    user = get_user_by_id(db, token_data.user_id)
    return user


async def get_current_user_required(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """取得目前登入的用戶（必須）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="無法驗證憑證",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    token_data = decode_token(token)
    if not token_data or not token_data.user_id:
        raise credentials_exception

    user = get_user_by_id(db, token_data.user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用戶已被停用"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user_required)
) -> User:
    """取得目前活躍的用戶"""
    return current_user
