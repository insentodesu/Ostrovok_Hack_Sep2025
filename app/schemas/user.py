from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None


class UserRead(UserBase):
    id: int
    role: str

    model_config = ConfigDict(from_attributes=True)
