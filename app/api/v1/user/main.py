from fastapi import APIRouter,Depends
from passlib.context import CryptContext


from passlib.context import CryptContext
from api.model.user import UserModel
from databases import get_db
from sqlalchemy.orm import Session
from typing import List
from api.schemas.user.main import UserCreate,UserOut
from api.authenticator.main import get_current_user
router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_users(db: Session):
    return db.query(UserModel).all()

def get_password_hash(password):
    return pwd_context.hash(password)

def get_users(db: Session):
    return db.query(UserModel).all()

@router.get("/users",response_model=List[UserOut])
def read_users( db: Session = Depends(get_db)):
    users = get_users(db=db)
    users_out = [UserOut(
        id=user.id.hex,
        name=user.name,
        email=user.email,
        description=user.description,
        created_at=user.created_at,
        updated_at=user.updated_at
    ) for user in users]
    return users_out

@router.post("/users", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    new_user = UserModel(name=user.name, email=user.email, password=hashed_password, description=user.description)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserOut(
        id=new_user.id.hex,
        name=new_user.name,
        email=new_user.email,
        description=new_user.description,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at
        )

@router.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: UserModel = Depends(get_current_user)):

    return UserOut(
        id=current_user.id.hex,
        name=current_user.name,
        email=current_user.email,
        description=current_user.description,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
        )


@router.patch("/users")
async def create_user():
    return {"message": "patch_user"}


@router.delete("/users")
async def create_user():
    return {"message": "delete_user"}

