from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user, get_db
from app.schemas.user import UserOut, UserUpdate
from sqlalchemy.orm import Session
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=UserOut)
def get_me(current: User = Depends(get_current_user)):
    return current

@router.put("/me/update", response_model=UserOut)
def update_me(
        payload: UserUpdate,
        db: Session = Depends(get_db),
        current: User = Depends(get_current_user)
):
    if payload.email and payload.email != current.email:
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=400, detail="Email già registrata")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(current, field, value)
    db.commit()
    db.refresh(current)
    return current