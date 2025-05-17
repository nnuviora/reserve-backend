from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from api.routers import routers as api_routers

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

def get_application() -> FastAPI:

    async def startup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    application = FastAPI()

    application.add_event_handler("startup", startup)

    origins = [
        "https://nuviora.vercel.app",
        "https://nuviora-frontend-git-dev-nnuvioras-projects.vercel.app",
        "http://localhost:8000",
    ]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in api_routers:
        application.include_router(router=router)

    return application


app = get_application()
