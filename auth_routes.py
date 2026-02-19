from fastapi import APIRouter, HTTPException, status
from .schemas.auth_models import UserSignup, UserLogin
from .auth_service import create_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
async def signup(payload: UserSignup):
    try:
        created = create_user(payload)
        return {"status": "ok", "user": created}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login")
async def login(payload: UserLogin):
    try:
        token_data = authenticate_user(payload)
        return token_data
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
