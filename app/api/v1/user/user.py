from fastapi import APIRouter

router = APIRouter()

@router.get("/user")
async def get_user():
    return {"message": "get_user"}


@router.post("/user")
async def create_user():
    return {"message": "create_user"}

@router.patch("/user")
async def create_user():
    return {"message": "patch_user"}


@router.delete("/user")
async def create_user():
    return {"message": "delete_user"}