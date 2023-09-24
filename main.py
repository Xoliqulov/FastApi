from datetime import timedelta, datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from jose import jwt
from pydantic import BaseModel

from db import User, SessionLocal

app = FastAPI()

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


class UserCreate(BaseModel):
    username: str
    first_name: str
    last_name: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None


def create_jwt_token(data, expires_delta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt


@app.get("/users/", response_model=List[UserResponse])
def get_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return users


@app.post("/users/", response_model=dict)
def create_user(user: UserCreate):
    db = SessionLocal()
    user_data = user.dict()

    access_token = create_jwt_token(user_data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_jwt_token(user_data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {
        "user": user_data,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@app.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate):
    db = SessionLocal()
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.first_name is not None:
        db_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        db_user.last_name = user_update.last_name
    if user_update.password is not None:
        db_user.password = user_update.password

    db.commit()
    db.refresh(db_user)
    db.close()
    return db_user


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    db = SessionLocal()
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    db.close()
    return {"message": "User deleted"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
