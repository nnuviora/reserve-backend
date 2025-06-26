from .v1.endpoints.health import router as health_router
from .v1.endpoints.auth import router as auth_router
from .v1.endpoints.user_profile import router as one_user_router
from .v1.endpoints.avatar import router as avatar_router
from .v1.endpoints.product import router as product_router
from .v1.endpoints.add_product import router as add_product_router


routers = [
    health_router,
    auth_router,
    one_user_router,
    avatar_router,
    product_router,
    add_product_router,
]
