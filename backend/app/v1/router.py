from fastapi import APIRouter

from app.v1.routes.health import router as health_router

router = APIRouter(prefix="/api/v1")

router.include_router(health_router)

# TODO(candidate): mount your massing / options routers here, e.g.
#   from app.v1.routes.massing import router as massing_router
#   router.include_router(massing_router)
