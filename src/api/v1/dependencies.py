from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException

from services.auth_service import AuthService
from services.user_service import UserService
from repositories.user_repo import UserRepository, TokenRepository
from core.security import JWTAuth
from utils.cache_manager import RedisManager
from utils.template_render import get_template

from utils.email_manager import MetaUaSender
from services.load_service import LoadService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def auth_dep() -> AuthService:
    try:
        # print("🔧 auth_dep: створення AuthService...")
        service = AuthService(
            user_repo=UserRepository,
            refresh_repo=TokenRepository,
            cache_manager=RedisManager,
            email_manager=MetaUaSender,
            security_layer=JWTAuth,
            error_handler=HTTPException,
            template_handler=get_template,
        )
        # print("✅ auth_dep: успішно створено")
        return service
    except Exception as e:
        print("❌ auth_dep помилка:", e)
        raise e

# async def auth_dep() -> AuthService:
#     return AuthService(
#         user_repo=UserRepository,
#         refresh_repo=TokenRepository,
#         cache_manager=RedisManager,
#         email_manager=MetaUaSender,
#         security_layer=JWTAuth,
#         error_handler=HTTPException,
#         template_handler=get_template,
#     )


# email_manager=AwsSender,


async def user_dep() -> UserService:
    return UserService(
        user_repo=UserRepository(),
        error_handler=HTTPException,
        token_repo=TokenRepository(),
    )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    service=Depends(auth_dep),
):
    try:
        payload = await service.security_layer.decode_token(token=token)
        if not payload:
            raise HTTPException(status_code=401, detail="Несанкціонований доступ")

        user_id = payload.get("id")

        user = await service.user_repo.get(id=user_id)
        if user is None or user is False:
            raise HTTPException(status_code=404, detail="Користувача не знайдено")
        return user
    except ValueError:
        raise HTTPException(status_code=401, detail="Несанкціонований доступ")

async def get_load_service() -> LoadService:
    return LoadService()


