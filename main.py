from typing import Optional, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from db import User, SessionLocal

app = FastAPI()


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


@app.get("/users/", response_model=List[UserResponse])
def get_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return users


@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate):
    db = SessionLocal()
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    db.close()
    return db_user


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
