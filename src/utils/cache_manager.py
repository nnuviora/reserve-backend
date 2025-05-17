import uuid
from datetime import datetime
import json
from abc import ABC, abstractmethod

from redis import Redis

from config import config_setting


class AbstractCache(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    async def set(self, token: str, data: dict, exp: int) -> str:
        pass

    @abstractmethod
    async def get(self, token: str) -> dict:
        pass

    @abstractmethod
    async def delete(self, token: str) -> bool:
        pass

class RedisManager(AbstractCache):
    def __init__(self) -> None:
        self.redis = Redis(
            host=config_setting.REDIS_HOST,
            port=config_setting.REDIS_PORT,
            password=config_setting.REDIS_PASSWORD,  # ДОДАНО
            decode_responses=True  # байти -> str
        )

    async def set(self, token: str, data: dict, exp: int) -> str:
        try:
            if isinstance(data, dict):
                data = {
                    k: str(v) if isinstance(v, (uuid.UUID, datetime)) else v
                    for k, v in data.items()
                }
            self.redis.set(token, json.dumps(data))
            if exp:
                self.redis.expire(token, exp)
            return token
        except Exception as e:
            raise Exception(f"Redis Set Error in {self.set.__name__}: {e}")

    async def get(self, token: str) -> dict:
        try:
            data = self.redis.get(token)
            if data:
                return json.loads(data)
        except Exception as e:
            raise Exception(f"Redis Get Error in {self.get.__name__}: {e}")

    async def delete(self, token: str) -> bool:
        try:
            self.redis.delete(token)
        except Exception as e:
            raise Exception(f"Redis Delete Error in {self.delete.__name__}: {e}")

# class RedisManager(AbstractCache):
#     def __init__(self) -> None:
#         self.redis = Redis(
#             host=config_setting.REDIS_HOST,
#             port=config_setting.REDIS_PORT,
#         )

#     async def set(self, token: str, data: dict, exp: int) -> str:
#         try:
#             if isinstance(data, dict):
#                 data = {
#                     k: str(v) if isinstance(v, (uuid.UUID, datetime)) else v
#                     for k, v in data.items()
#                 }
#             self.redis.set(
#                 token,
#                 json.dumps(data),
#             )
#             if exp:
#                 self.redis.expire(token, exp)
#             return token
#         except Exception as e:
#             raise Exception(f"Redis Set Error in {self.set.__name__}: {e}")

#     async def get(self, token: str) -> dict:
#         try:
#             data = self.redis.get(token)
#             if data:
#                 return json.loads(data)
#         except Exception as e:
#             raise Exception(f"Redis Get Error in {self.get.__name__}: {e}")

#     async def delete(self, token: str) -> bool:
#         try:
#             self.redis.delete(token)
#         except Exception as e:
#             raise Exception(f"Redis Delete Error in {self.delete.__name__}: {e}")
