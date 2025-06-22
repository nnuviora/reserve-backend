from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import config_setting


engine = create_async_engine(config_setting.DB_URI)
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
