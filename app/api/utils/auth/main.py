from sqlalchemy.orm import Session
from passlib.context import CryptContext
from api.model.user import UserModel
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_users(db: Session):
    return db.query(UserModel).all()

def get_password_hash(password):
    return pwd_context.hash(password)