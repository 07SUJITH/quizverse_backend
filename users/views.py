import secrets
import re
from datetime import datetime, timedelta

from ninja import Router, Form
from typing import Any, List
from pydantic import EmailStr

from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q

from users.models import *
from users.schemas import *
from quizverse_backend.settings import PASSWORD_REGEX, EMAIL_HOST_USER
from utils.authentication import (
    AuthBearer,
    role_required,
    verify_token,
    generate_access_token,
    generate_token,
)

router = Router(auth=AuthBearer())


def otp_generator(length):
    return secrets.randbelow(10**length)

def verification_email(email):
    otp = otp_generator(6)
    subject = "Email Verification"
    message = f"Your OTP is {otp}. Please verify your email."
    from_email = EMAIL_HOST_USER
    recipient_list = [email]

    send_mail(subject, message, from_email, recipient_list)
    return otp


@router.get("/user", response={200: UserOutSchema, 404: Any})
def get_user(request):
    try:
        user = User.objects.get(id=request.auth.user_id)
        return 200, user
    except User.DoesNotExist:
        return 404, {"details": "User not found"}


@router.get("/users", response={201: List[UserOutSchema]})
@role_required(["Admin"])
def get_users(request):
    users = User.objects.all()
    return 201, users


@router.post("/register/", response={201: UserOutSchema, 400: Any})
def register(request, user: UserInSchema):
    unique_fields = ["username", "email"]
    user_data = user.dict()
    for field in unique_fields:
        if User.objects.filter(**{field: user_data[field]}).exists():
            return 400, {"details": f"{field} already exists"}
    if not re.match(PASSWORD_REGEX, user_data["password"]):
        return 400, {
            "details": """Password is weak and must contain 
            at least 8 characters, 1 uppercase, 1 lowercase, 
            1 number and 1 special character"""
        }
    user_data["password"] = make_password(user_data["password"])
    user = User.objects.create(**user_data)
    otp = verification_email(user.email)
    VerificationToken.objects.create(user=user, otp=otp, token_type="verify")
    return 201, user


@router.post("/verify/", response={200: Any, 400: Any})
def send_verification(request):
    user_id = request.auth.user_id
    user = User.objects.get(id=user_id)
    if user.is_verified:
        return 400, {"details": "Email already verified"}

    otp = verification_email(user.email)
    VerificationToken.objects.create(user=user, otp=otp, token_type="verify")
    return 200, {"details": "Verification email sent"}


@router.post("/verify/{otp}/", response={200: Any, 400: Any})
def verify_otp(request, otp: int):
    user_id = request.auth.user_id
    user = User.objects.get(id=user_id)
    try:
        verification_token = VerificationToken.objects.get(user=user)
    except VerificationToken.DoesNotExist:
        return 400, {"details": "No otp found"}
    if datetime.now() > verification_token.created_at + timedelta(minutes=5):
        return 400, {"details": "OTP expired"}
    if verification_token.token_type != "verify":
        return 400, {"details": "Invalid otp type"}

    user.is_verified = True
    user.save()
    verification_token.delete()
    return 200, {"details": "Email verified"}


@router.post("/login/", auth=None, response={200: TokenSchema, 400: Any})
def login(request, login: LoginSchema):
    user_data = login.dict()
    user = User.objects.filter(
        Q(username=user_data["username_or_email"])
        | Q(email=user_data["username_or_email"])
    ).first()

    if user and check_password(user_data["password"], user.password):
        access_token, refresh_token = generate_token(
            user.id, [role.name for role in user.role.all()]
        )
        return 200, {"access_token": access_token, "refresh_token": refresh_token}

    return 400, {"details": "Invalid credentials"}


@router.post("/logout/", response={200: Any, 400: Any})
def logout(request):
    data = request.auth
    Token.objects.filter(user_id=data["user_id"], access_token=data["token"]).delete()
    return 200, {"message": "Logout successful"}


@router.post("/get-access-token/", response={200: TokenSchema, 400: Any})
def get_access_token(request, refresh_token: str = Form(...)):
    try:
        payload = verify_token(refresh_token, "refresh")
        if payload is None:
            return 400, {
                "message": "Invalid token",
                "code": 400,
                "details": {"error": "Token is invalid or expired"},
            }
        user_id = payload["user_id"]
        role = payload["role"]
        access_token = generate_access_token(user_id, role)
        Token.objects.filter(user_id=user_id, refresh_token=refresh_token).update(
            access_token=access_token
        )
        return 200, {"access_token": access_token, "refresh_token": refresh_token}
    except Exception as e:
        return 400, {
            "message": "Invalid token",
            "code": 400,
            "details": {"error": str(e)},
        }


@router.post("/reset-password/", response={200: Any, 400: Any, 500: Any})
def reset_password(request, payload: ResetPasswordSchema):
    user = User.objects.get(id=request.auth["user_id"])
    if not check_password(payload.current_password, user.password):
        return 400, {
            "message": "Invalid current password",
            "code": 400,
            "details": {"current_password": ["Password is incorrect"]},
        }
    if check_password(payload.new_password, user.password):
        return 400, {
            "message": "Invalid new password",
            "code": 400,
            "details": {"new_password": ["New password must be different"]},
        }
    user.password = make_password(payload.new_password)
    user.save()
    return 200, {"message": "Reset password successful"}


@router.post("/forgot-password/", auth=None, response={200: Any, 400: Any})
def forgot_password(request, email: EmailStr = Form(...)):
    user = User.objects.filter(email=email).first()
    if user:
        otp = otp_generator(6)
        VerificationToken.objects.create(user=user, otp=otp, token_type="forgot")
        subject = "Forgot Password"
        message = f"Your OTP is {otp}. Please reset your password."
        from_email = EMAIL_HOST_USER
        recipient_list = [email]

        send_mail(subject, message, from_email, recipient_list)
        return 200, {"message": "Email sent"}
    return 400, {"message": "Email not found"}


@router.post("/forgot-password/{otp}/", auth=None, response={200: Any, 400: Any})
def verify_forgot_otp(request, otp: int, new_password: str = Form(...)):
    try:
        verification_token = VerificationToken.objects.get(otp=otp)
    except VerificationToken.DoesNotExist:
        return 400, {"details": "Invalid token"}
    if datetime.now() > verification_token.created_at + timedelta(minutes=2):
        return 400, {"details": "OTP expired"}
    if verification_token.token_type != "forgot":
        return 400, {"details": "Invalid otp type"}
    token = secrets.token_urlsafe(40)
    ResetFormToken.objects.create(user=verification_token.user, token=token)
    verification_token.delete()
    
    return 200, {"message": "OTP verified successfully", "token": token}

@router.post("/reset-forgot-password/{token}/", auth=None, response={200: Any, 400: Any})
def reset_forgot_password(request, token: str, new_password: str = Form(...)):
    try:
        reset_token = ResetFormToken.objects.get(token=token)
    except ResetFormToken.DoesNotExist:
        return 400, {"details": "Invalid token"}
    if datetime.now() > reset_token.created_at + timedelta(minutes=10):
        return 400, {"details": "OTP expired"}
    user = reset_token.user
    user.password = make_password(new_password)
    user.save()
    reset_token.delete()
    return 200, {"message": "Password reset successful"}