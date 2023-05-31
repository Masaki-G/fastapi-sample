from fastapi import APIRouter

from api.v1.user import router as user_router

router = APIRouter(
    prefix='/api/v1',
    tags=['user']
)

router.include_router(user_router)
