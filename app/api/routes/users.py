from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.schemas.user import UserOut, UserUpdate
from sqlalchemy.orm import Session
from app.api.deps import get_db
from fastapi import HTTPException
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
    # Email deve essere unica!
    if payload.email and payload.email != current.email:
        exist = db.query(User).filter(User.email == payload.email).first()
        if exist:
            raise HTTPException(status_code=400, detail="Email già registrata")

    # Aggiorna solo i campi presenti
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(current, field, value)
    db.commit()
    db.refresh(current)
    return current