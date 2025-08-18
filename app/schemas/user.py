from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

class UserUpdate(BaseModel):
    full_name: str | None = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True