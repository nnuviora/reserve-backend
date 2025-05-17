from abc import ABC, abstractmethod
from typing import Any
from sqlalchemy import select
from database import async_session_maker
from utils.logging import get_logger


class AbstractRepository(ABC):
    model = None

    @abstractmethod
    async def insert(self, data: dict) -> dict:
        pass

    @abstractmethod
    async def get(self, *args: Any, **kwargs: Any) -> dict:
        pass

    @abstractmethod
    async def get_all(self, *args: Any, **kwargs: Any) -> list[dict]:
        pass

    @abstractmethod
    async def update(self, data: dict, *args: Any, **kwargs: Any) -> dict:
        pass

    @abstractmethod
    async def delete(self, *args: Any, **kwargs: Any) -> bool:
        pass


class SqlLayer(AbstractRepository):
    model = None

    async def insert(self, data: dict) -> dict:
        async with async_session_maker() as session:
            try:
                stmt = self.model(**data)
                session.add(stmt)
                await session.commit()
                get_logger().info(
                    f"DATA INSERTED: {self.model.__name__} with data: {data}"
                )
                await session.refresh(stmt)
                return await stmt.to_dict()
            except Exception as e:
                get_logger().error(f"ERROR INSERTING: {self.model.__name__}: {e}")
                await session.rollback()
                raise Exception(f"Insert Error in {self.model.__class__.__name__}: {e}")

    async def get(self, *args: Any, **kwargs: Any) -> dict:
        async with async_session_maker() as session:
            try:
                stmt = select(self.model).filter_by(**kwargs)
                res = await session.execute(stmt)
                res = res.scalar_one_or_none()
                if res is None:
                    return None
                get_logger().info(
                    f"DATA GET: {self.model.__name__} with data: {args}, {kwargs}"
                )
                return await res.to_dict()
            except Exception as e:
                get_logger().info(
                    f"DATA NOT GET: {self.model.__name__} with data: {args}, {kwargs}"
                )
                raise Exception(f"Get Error in {self.model.__class__.__name__}: {e}")

    async def get_all(self, *args: Any, **kwargs: Any) -> list[dict]:
        async with async_session_maker() as session:
            try:
                stmt = select(self.model).filter_by(**kwargs)
                res = await session.execute(stmt)
                get_logger().info(
                    f"DATA ALL GET: {self.model.__name__} with data: {args}, {kwargs}"
                )
                return [await row.to_dict() for row in res.scalars().all() if row]
            except Exception as e:
                get_logger().info(
                    f"DATA NOT ALL GET: {self.model.__name__} with data: {args}, {kwargs}"
                )
                raise Exception(
                    f"Get-all Error in {self.model.__class__.__name__}: {e}"
                )

    async def update(
        self,
        data: dict,
        *args: Any,
        **kwargs: Any,
    ) -> dict:
        async with async_session_maker() as session:
            try:
                stmt = await session.execute(select(self.model).filter_by(**kwargs))
                res = stmt.scalar_one_or_none()

                if not res:
                    return False

                for (
                    key,
                    value,
                ) in data.items():
                    setattr(res, key, value)

                await session.commit()
                await session.refresh(res)
                get_logger().info(
                    f"DATA UPDATED: {self.model.__name__} with data: {data}, {args}, {kwargs}"
                )
                return await res.to_dict()
            except Exception as e:
                await session.rollback()
                get_logger().info(
                    f"DATA NOT UPDATED: {self.model.__name__} with data: {data}, {args}, {kwargs}"
                )
                raise Exception(f"Update Error in {self.model.__class__.__name__}: {e}")

    async def delete(self, *args: Any, **kwargs: Any) -> bool:
        async with async_session_maker() as session:
            try:
                stmt = await session.execute(select(self.model).filter_by(**kwargs))
                res = stmt.scalars().all()  # new libe added
                # res = stmt.scalar_one_or_none()

                for one_res in res:
                    await session.delete(one_res)

                if not res:
                    return False

                # await session.delete(res)
                await session.commit()
                get_logger().info(
                    f"DATA DELETED: {self.model.__name__} with data: {args}, {kwargs}"
                )
                return True
            except Exception as e:
                await session.rollback()
                get_logger().info(
                    f"DATA NOT DELETED: {self.model.__name__} with data: {args}, {kwargs}"
                )
                raise Exception(f"Delete Error in {self.model.__class__.__name__}: {e}")
