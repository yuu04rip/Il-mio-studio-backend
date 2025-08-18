from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas.user import UserOut, UserUpdate, PasswordChange
from app.core.security import verify_password, hash_password
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=UserOut)
def get_me(current: User = Depends(get_current_user)):
    return current

@router.put("/me", response_model=UserOut)
def update_me(data: UserUpdate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if data.full_name is not None:
        current.full_name = data.full_name
    db.add(current)
    db.commit()
    db.refresh(current)
    return current

@router.put("/me/password")
def change_password(data: PasswordChange, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if not verify_password(data.old_password, current.hashed_password):
        return {"ok": False, "detail": "Old password incorrect"}
    current.hashed_password = hash_password(data.new_password)
    db.add(current)
    db.commit()
    return {"ok": True}