from fastapi import APIRouter
from api.model.user import UserModel
from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends,HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from api.model.user import UserModel
from databases import get_db
from typing import Optional
from sqlalchemy.orm import Session

from ..schemas.auth.main import TokenWithRefresh, RefreshToken, UserWithPassword,Token
from ..schemas.user.main import UserIn

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60



@router.post("/login", response_model=TokenWithRefresh)
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


@router.post("/token/refresh", response_model=Token)
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

# JWTリフレッシュトークンを作成
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)  # 30 days for refresh token
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


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