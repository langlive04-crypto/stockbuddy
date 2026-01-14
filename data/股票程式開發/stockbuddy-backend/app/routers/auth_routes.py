"""
auth_routes.py - 身份驗證 API 路由
V10.38: 新增用戶註冊、登入、登出功能

端點：
- POST /api/auth/register - 用戶註冊
- POST /api/auth/login - 用戶登入
- GET /api/auth/me - 取得目前用戶資訊
- PUT /api/auth/me - 更新目前用戶資訊
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db, User
from ..services.auth_service import (
    Token,
    UserCreate,
    UserResponse,
    create_user,
    authenticate_user,
    create_access_token,
    get_user_by_username,
    get_current_user,
    get_current_user_required,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    用戶註冊

    - **username**: 用戶名稱 (必填，唯一)
    - **password**: 密碼 (必填，至少 6 字元)
    - **email**: 電子郵件 (選填)
    """
    # 檢查用戶名稱是否已存在
    existing_user = get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用戶名稱已被使用"
        )

    # 驗證密碼長度
    if len(user.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密碼至少需要 6 個字元"
        )

    # 建立用戶
    db_user = create_user(db, user)
    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用戶登入

    使用 OAuth2 表單格式：
    - **username**: 用戶名稱
    - **password**: 密碼

    回傳 JWT Token
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶名稱或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用戶已被停用"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user_required)
):
    """
    取得目前登入的用戶資訊

    需要 Bearer Token 認證
    """
    return current_user


@router.get("/check")
async def check_auth_status(
    current_user: User = Depends(get_current_user)
):
    """
    檢查認證狀態

    回傳目前是否已登入，以及用戶基本資訊（如果已登入）
    """
    if current_user:
        return {
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email
            }
        }
    return {"authenticated": False, "user": None}


@router.put("/me")
async def update_current_user(
    email: str = None,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    更新目前用戶資訊

    目前只支援更新 email
    """
    if email:
        current_user.email = email
        db.commit()
        db.refresh(current_user)

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    變更密碼

    - **old_password**: 目前密碼
    - **new_password**: 新密碼 (至少 6 字元)
    """
    from ..services.auth_service import verify_password, get_password_hash

    # 驗證舊密碼
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目前密碼錯誤"
        )

    # 驗證新密碼長度
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密碼至少需要 6 個字元"
        )

    # 更新密碼
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()

    return {"message": "密碼已更新"}
