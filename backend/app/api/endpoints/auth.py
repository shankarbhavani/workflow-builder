"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import create_access_token, get_current_user
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """
    Login endpoint - hardcoded credentials for POC
    Username: admin
    Password: admin
    """

    # Hardcoded authentication for POC
    if login_data.username != "admin" or login_data.password != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": login_data.username})

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(username=current_user["username"])
