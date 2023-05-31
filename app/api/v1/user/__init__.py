from fastapi import APIRouter

from api.v1.user import user

router = APIRouter(
    tags=['user']
)

router.include_router(user.router)
