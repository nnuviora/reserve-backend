import uuid
import random
import asyncio
from datetime import datetime
from typing import Protocol, Optional
from fastapi import UploadFile

from utils.repository import AbstractRepository
from utils.cache_manager import AbstractCache
from utils.email_manager import AbstractEmail
from services.s3_avatar_uploader import S3AvatarUploader

# class AuthService(Protocol):
class AuthService:
    def __init__(
        self,
        user_repo,
        refresh_repo,
        cache_manager,
        email_manager,
        security_layer,
        error_handler,
        template_handler,
    ) -> None:
        self.user_repo: AbstractRepository = user_repo()
        self.refresh_repo: AbstractRepository = refresh_repo()
        self.cache_manager: AbstractCache = cache_manager()
        self.email_manager: AbstractEmail = email_manager()
        self.security_layer = security_layer()
        self.error_handler = error_handler
        self.template_handler = template_handler

    async def send_mail(self, recipient: str, subject: str, body_text: str) -> None:
        try:
            await self.email_manager.send_email(
                recipient=recipient,
                subject=subject,
                body_text=body_text,
            )
        except Exception:
            raise self.error_handler(status_code=504, detail="Gateway Timeout")

    async def _generate_verification_token(
        self,
        data: dict,
        template: str = "verify_email_template.html",
        exp: int = None,
    ) -> str:
        try:
            token = str(random.randint(1000, 9999))
            html_page = await self.template_handler(
                template_name=template,
                context={"year": datetime.now().year, "code": token},
            )
            if not data.get("count"):
                data["count"] = 0
            cache_data = await self.cache_manager.set(token=token, data=data, exp=exp)
            await self.cache_manager.set(
                token=str(data.get("id")), data=cache_data, exp=exp
            )
            await self.send_mail(
                recipient=data.get("email"),
                subject="Email Verification",
                body_text=html_page,
            )
            return token
        except Exception as e:
            raise e

    async def resend_email(self, user_id: uuid.UUID):
        try:
            token = await self.cache_manager.get(token=str(user_id))
            data = await self.cache_manager.get(token=token)

            if not data:
                raise self.error_handler(
                    status_code=400, detail="Токен підтвердження електронної пошти протермінований"
                )

            await asyncio.gather(
                self.cache_manager.delete(token=token),
                self.cache_manager.delete(token=str(user_id)),
            )

            if data.get("count") >= 3:
                raise self.error_handler(status_code=429, detail="Забагато запитів")

            data["count"] += 1
            new_token = await self._generate_verification_token(data, exp=180)
            return {"message": "Повідомлення надіслано", "id": user_id}
        except self.error_handler as e:
            raise e
        except Exception as e:
            raise self.error_handler(status_code=500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

    async def create_handler(self, data: dict) -> dict:
        try:
            if data.get("auth_type") == "local":
                user_obj = await self.user_repo.get(email=data.get("email"))
                if user_obj:
                    raise self.error_handler(
                        status_code=409, detail="Електронна пошта вже існує"
                    )

                if data.get("hash_password") != data.get("repeat_password"):
                    raise self.error_handler(
                        status_code=400, detail="Паролі не збігаються"
                    )

                data["id"] = uuid.uuid4()
                data["hash_password"] = await self.security_layer.hash_password(
                    password=data.get("hash_password")
                )
                data.pop("repeat_password")
                token = await self._generate_verification_token(data=data, exp=180)
                return {"message": "Повідомлення надіслано", "id": data.get("id")}

            user_obj = await self.user_repo.get(email=data.get("email"))
            if not user_obj:
                user_obj = await self.user_repo.insert(
                    data={
                        "username": data.get("name"),
                        "email": data.get("email"),
                        "first_name": data.get("given_name"),
                        "last_name": data.get("family_name"),
                        "auth_type": data.get("auth_type"),
                    }
                )
            return await self._generate_token_pair(
                data=user_obj, user_agent=data.get("user_agent")
            )
        except self.error_handler as e:
            raise e
        except Exception as e:
            # import traceback
            # traceback.print_exc()  # ← або logger.error(traceback.format_exc())
            raise self.error_handler(status_code=500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

    async def _generate_token_pair(self, data: dict, user_agent: Optional[str]) -> dict:
        try:
            access_token = await self.security_layer.create_access_token(
                data={"id": str(data.get("id"))}
            )

            refresh_token, expire = await self.security_layer.create_refresh_token(
                data={"id": str(data.get("id"))}
            )
            refresh_token = await self.refresh_repo.insert(
                data={
                    "user_id": data.get("id"),
                    "refresh_token": refresh_token,
                    "user_agent": user_agent,
                    "expires_at": expire,
                }
            )
            return {
                "access_token": access_token,
                "refresh_token": refresh_token.get("refresh_token"),
            }
        except Exception as e:
            raise self.error_handler(status_code=500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

    async def email_verify_handler(self, data: dict) -> dict:
        try:
            user_obj = await self.cache_manager.get(token=data.get("token"))
            if not data:
                raise self.error_handler(
                    status_code=400, detail="Токен підтвердження електронної пошти протермінований"
                )

            user_obj.pop("count")
            user_obj = await self.user_repo.insert(data=user_obj)
            await self.cache_manager.delete(token=data.get("token"))
            token_pair = await self._generate_token_pair(
                data=user_obj, user_agent=data.get("user_agent")
            )
            return token_pair
        except self.error_handler as e:
            raise e
        except Exception as e:
            raise self.error_handler(status_code=500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

    async def user_verify_handler(self, token: str):
        try:
            data = await self.cache_manager.get(token=token)
            if not data:
                raise self.error_handler()

            await self.cache_manager.delete(token=token)
            await self.cache_manager.set(token=token, data=data, exp=180)
            await self.cache_manager.set(token=str(data.get("id")), data=token, exp=180)
            return {"message": "Користувача успішно підтверджено"}
        except Exception:
            raise self.error_handler(status_code=500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

    async def forgot_password_handler(self, data: dict) -> dict:
        try:
            user_obj = await self.user_repo.get(email=data.get("email"))
            if not user_obj:
                raise self.error_handler(status_code=404, detail="Користувача не знайдено")

            token = await self._generate_verification_token(data=user_obj, exp=180)
            return {"message": "Повідомлення надіслано", "id": user_obj.get("id")}
        except self.error_handler as e:
            raise e
        except Exception as e:
            raise self.error_handler(status_code=500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

    async def change_password_handler(self, data: dict) -> dict:
        try:
            if data.get("hash_password") != data.get("repeat_password"):
                raise self.error_handler(
                    status_code=401, detail="Паролі не збігаються"
                )

            token = await self.cache_manager.get(token=str(data.get("id")))
            user_obj = await self.cache_manager.get(token=token)

            if not user_obj:
                raise self.error_handler(status_code=400, detail="Час вичерпано")

            user_obj = await self.user_repo.update(
                id=user_obj.get("id"),
                data={
                    "update_at": datetime.now(),
                    "hash_password": await self.security_layer.hash_password(
                        password=data.get("hash_password")
                    ),
                },
            )
            token_pair = await self._generate_token_pair(
                data=user_obj, user_agent=data.get("user_agent")
            )
            return {"message": "Пароль успішно змінено"}
        except self.error_handler as e:
            raise e
        except Exception as e:
            raise self.error_handler(status_code=500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

    async def login_handler(self, data: dict) -> dict:
        try:
            user_obj = await self.user_repo.get(email=data.get("email"))
            if not user_obj or not (
                await self.security_layer.verify_password(
                    password=data.get("password"),
                    hash_password=user_obj.get("hash_password"),
                )
            ):
                raise self.error_handler(
                    status_code=400, detail="Недійсне ім'я користувача або пароль"
                )

            token_pair = await self._generate_token_pair(
                data=user_obj, user_agent=data.get("user_agent")
            )
            return token_pair
        except self.error_handler as e:
            raise e
        except Exception as e:
            raise self.error_handler(status_code=500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

    async def recreate_access_handler(self, data: dict) -> dict:
        try:
            payload = await self.security_layer.decode_token(
                token=data.get("refresh_token")
            )
            if not payload:
                raise self.error_handler(status_code=401, detail="Несанкціонований доступ")

            user_obj = await self.user_repo.get(id=payload.get("id"))
            if not user_obj:
                raise self.error_handler(status_code=404, detail="User not found")

            await self.refresh_repo.delete(refresh_token=data.get("refresh_token"))
            return await self._generate_token_pair(
                data=payload, user_agent=data.get("user_agent")
            )
        except self.error_handler as e:
            raise e
        except ValueError:
            raise self.error_handler(status_code=410, detail="Видалено")
        except Exception as e:
            raise self.error_handler(status_code=500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

    async def logout_handler(self, refresh_token: str) -> dict:
        try:
            await self.refresh_repo.delete(refresh_token=refresh_token)
            return {"message": "Вихід успішний"}
        except Exception:
            raise self.error_handler(status_code=500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

    async def delete_test(self, email: str):
        user_obj = await self.user_repo.get(email=email)
        tokens = await self.refresh_repo.get_all(user_id=user_obj["id"])

        for token in tokens:
            await self.refresh_repo.delete(id=token["id"])

        await self.user_repo.delete(id=user_obj["id"])

    # async def update_avatar_handler(self, user_id: uuid.UUID, file: UploadFile) -> dict:
    #     try:
    #         # Завантажуємо аватар на S3
    #         uploader = S3AvatarUploader()
    #         contents = await file.read()
    #         avatar_url = uploader.upload_avatar(
    #             file_bytes=contents,
    #             filename=file.filename,
    #             content_type=file.content_type
    #         )

    #         # Оновлюємо аватар в базі даних через репозиторій
    #         updated_user = await self.user_repo.update_avatar(user_id=user_id, avatar_url=avatar_url)

    #         return {"message": "Avatar updated successfully", "user": updated_user}
    #     except Exception as e:
    #         raise self.error_handler(status_code=500, detail="Failed to update avatar")
