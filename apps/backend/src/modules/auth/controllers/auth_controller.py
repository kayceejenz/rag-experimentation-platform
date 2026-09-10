from typing import Annotated

from api.dependencies import auth_rate_limiter, auth_service, current_user, settings
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from modules.auth.dtos.login_dto import LoginRequest
from modules.auth.dtos.register_dto import RegisterRequest
from modules.auth.dtos.token_dto import TokenResponse
from modules.auth.dtos.user_dto import UserResponse
from modules.auth.models.auth_user_model import AuthenticatedUser
from modules.auth.models.error_model import (
    AccountAlreadyExistsError,
    AuthRateLimitExceededError,
    InvalidCredentialsError,
    InvalidInvitationCodeError,
    InvalidRefreshTokenError,
)
from modules.auth.models.token_model import TokenPair
from modules.auth.services.auth_service import AuthenticationService
from modules.auth.services.rate_limit_service import AuthRateLimiter

router = APIRouter(prefix="/auth", tags=["authentication"])


def enforce_auth_rate_limit(
    request: Request,
    limiter: AuthRateLimiter,
    action: str,
) -> None:
    client_identifier = request.client.host if request.client else "unknown"
    try:
        limiter.check(action, client_identifier)
    except AuthRateLimitExceededError as error:
        raise HTTPException(
            429,
            "Too many authentication attempts. Please try again later.",
            headers={"Retry-After": str(error.retry_after_seconds)},
        ) from None


def set_refresh_cookie(response: Response, pair: TokenPair) -> None:
    c = settings()
    response.set_cookie(
        "refresh_token",
        pair.refresh_token,
        max_age=c.refresh_token_days * 86400,
        httponly=True,
        secure=c.app_env == "production",
        samesite="strict",
        path="/api/v1/auth",
    )


def token_response(pair: TokenPair) -> TokenResponse:
    return TokenResponse(
        access_token=pair.access_token,
        token_type=pair.token_type,
        expires_in=pair.access_token_expires_in,
    )


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    body: RegisterRequest,
    request: Request,
    service: Annotated[AuthenticationService, Depends(auth_service)],
    limiter: Annotated[AuthRateLimiter, Depends(auth_rate_limiter)],
):
    enforce_auth_rate_limit(request, limiter, "register")
    try:
        user = service.register(
            body.email,
            body.password,
            body.display_name,
            body.invitation_code,
        )
    except InvalidInvitationCodeError:
        raise HTTPException(403, "A valid invitation code is required") from None
    except AccountAlreadyExistsError:
        raise HTTPException(409, "Account already exists") from None
    return UserResponse(
        id=str(user.id), email=user.email, display_name=user.display_name
    )


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    service: Annotated[AuthenticationService, Depends(auth_service)],
    limiter: Annotated[AuthRateLimiter, Depends(auth_rate_limiter)],
):
    enforce_auth_rate_limit(request, limiter, "login")
    try:
        pair = service.login(
            body.email,
            body.password,
            request.headers.get("user-agent"),
            request.client.host if request.client else None,
        )
    except InvalidCredentialsError:
        raise HTTPException(401, "Invalid email or password") from None
    set_refresh_cookie(response, pair)
    return token_response(pair)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    service: Annotated[AuthenticationService, Depends(auth_service)],
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    if not refresh_token:
        raise HTTPException(401, "Missing refresh token")
    try:
        pair = service.refresh(refresh_token)
    except InvalidRefreshTokenError:
        response.delete_cookie("refresh_token", path="/api/v1/auth")
        raise HTTPException(401, "Invalid refresh token") from None
    set_refresh_cookie(response, pair)
    return token_response(pair)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    service: Annotated[AuthenticationService, Depends(auth_service)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> None:
    if refresh_token:
        service.logout(refresh_token)
    response.delete_cookie("refresh_token", path="/api/v1/auth")


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[AuthenticatedUser, Depends(current_user)]) -> UserResponse:
    return UserResponse(
        id=str(user.id), email=user.email, display_name=user.display_name
    )
