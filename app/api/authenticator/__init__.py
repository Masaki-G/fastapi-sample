from fastapi import APIRouter

from api.authenticator import main
router = APIRouter(
    tags=['auth']
)

router.include_router(main.router)