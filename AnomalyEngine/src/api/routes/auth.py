from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.utils.otp import generate_otp, get_otp_expiration, send_otp_email
from .. import crud, database, models, schemas, security
from ..dependencies import is_dev, get_current_user

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
):
    """Authenticate user and return JWT token."""
    print(f"Login attempt for username: {form_data.username}, with password: {form_data.password}")
    
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register/request", response_model=schemas.OTPRequestResponse)
def register_request(
    request: schemas.UserCreate,
    db: Session = Depends(database.get_db)
):
    """Public registration request that sends an OTP to the provided email."""
    existing_user = crud.get_user_by_username(db, request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    if crud.get_user_by_email(db, request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    if request.role and request.role != "analyst":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only analyst role can be self-registered. Contact an admin for higher privileges.",
        )

    user = crud.create_user(
        db,
        username=request.username,
        email=request.email,
        password=request.password,
        role="analyst",
        email_verified=False,
    )
    otp_code = generate_otp()
    expires_at = get_otp_expiration()
    crud.save_otp(db, request.email, otp_code, expires_at)
    send_otp_email(request.email, otp_code)
    return {
        "message": "OTP sent to email. Verify within 10 minutes.",
        "email": request.email,
        "user_id": user.id,
    }


@router.post("/register/verify", response_model=schemas.UserRead)
def verify_registration(
    request: schemas.OTPVerificationRequest,
    db: Session = Depends(database.get_db)
):
    """Verify OTP and complete registration."""
    if not crud.verify_otp(db, request.email, request.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )
    user = crud.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.post("/test/register/request", response_model=schemas.OTPRequestResponse)
def test_register_request(
    request: schemas.UserCreate,
    db: Session = Depends(database.get_db)
):
    """Test registration request (development only)."""
    if not is_dev():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test Registration is disabled in production",
        )
    
    existing_user = crud.get_user_by_username(db, request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    if crud.get_user_by_email(db, request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    if request.role and request.role != "analyst" and request.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only analyst and admin roles can be self-registered. Contact an admin for higher privileges.",
        )

    user = crud.create_user(
        db,
        username=request.username,
        email=request.email,
        password=request.password,
        role="analyst",
        email_verified=False,
    )
    otp_code = '123456'
    expires_at = get_otp_expiration()
    crud.save_otp(db, request.email, otp_code, expires_at)

    return {
        "message": "OTP sent to email. Verify within 10 minutes.",
        "email": request.email,
        "user_id": user.id,
    }


@router.post("/test/register/verify", response_model=schemas.UserRead)
def test_verify_registration(
    request: schemas.OTPVerificationRequest,
    db: Session = Depends(database.get_db)
):
    """Test OTP verification (development only)."""
    if not is_dev():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test Verification is disabled in production",
        )
    
    if not crud.verify_otp(db, request.email, request.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )
    user = crud.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("/me", response_model=schemas.UserRead)
def read_current_user(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get current authenticated user."""
    return current_user
