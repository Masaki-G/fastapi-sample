from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, UUID4, validator
from model.user import UserModel
from databases import get_db
from typing import Optional
from sqlalchemy.orm import Session


from typing import List
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60



class UserIn(BaseModel):
    email: str

class UserWithPassword(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    description: Optional[str] = None


class TokenWithRefresh(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshToken(BaseModel):
    refresh_token: str


# 引数のemailを元にDBからユーザーを取得
def get_user(db, email: str):
    return db.query(UserModel).filter(UserModel.email == email).first()

# 引数で渡されたパスワードとハッシュ化されたパスワードが一致するか確認
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# ユーザーがDBに保存されているか確認
def authenticate_user(db, email: str, password: str):
    user = get_user(db, email)
    # ユーザーが存在しない場合
    if not user:
        print("user not found")
        return False
    # パスワードが一致しない場合
    if not verify_password(password, user.password):
        print("password not match")
        return False
    print("user found")
    return user

# JWTトークンを作成
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
        print(expire)
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)  # 30 days for refresh token
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/login", response_model=TokenWithRefresh)
async def login_for_access_token(form_data: UserWithPassword, db: Session = Depends(get_db)):
    # ユーザーがDBに保存されているか確認
    user = authenticate_user(db, form_data.email, form_data.password)
    # ユーザーが存在しない場合
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    

    # JWTトークンを作成
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=30)  # Set the refresh token expiration time
    refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@app.post("/token/refresh", response_model=Token)
async def refresh_access_token(refresh_token: RefreshToken, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# JWTトークンを検証
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = UserIn(email=email)
    except JWTError:
        raise credentials_exception

    user = get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


# async def get_current_active_user(current_user: UserOut = Depends(get_current_user)):
#     print(current_user)
#     # if current_user.disabled:
#     #     raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user


# addUser


def get_password_hash(password):
    return pwd_context.hash(password)

@app.post("/users", response_model=UserOut)
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


def get_users(db: Session):
    return db.query(UserModel).all()

@app.get("/users",response_model=List[UserOut])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = get_users(db=db)
    users_out = [UserOut(
        id=user.id.hex,
        name=user.name,
        email=user.email,
        description=user.description,
        created_at=user.created_at,
        updated_at=user.updated_at
    ) for user in users[skip : skip + limit]]
    return users_out

@app.get("/users/me/", response_model=UserOut)
async def read_users_me(current_user: UserModel = Depends(get_current_user)):

    return UserOut(
        id=current_user.id.hex,
        name=current_user.name,
        email=current_user.email,
        description=current_user.description,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
        )

from api import v1
# エンドポイントのルーティング
app.include_router(v1.router)
