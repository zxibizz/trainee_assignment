"""Pydantic request/response schemas."""

from enum import Enum

from pydantic import BaseModel, Field


# ---- Users ----
class UserRole(str, Enum):
    """The set of roles a user account can hold."""

    ADMIN = "ADMIN"
    USER = "USER"


class User(BaseModel):
    username: str
    role: UserRole


# ---- Auth ----
class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ---- Products ----
class Product(BaseModel):
    id: int
    name: str
    section: str
    description: str = ""
    discount: float = 0.0
    price: float


class ProductCreate(BaseModel):
    name: str
    section: str
    description: str = ""
    discount: float = Field(default=0.0, ge=0, le=100)
    price: float = Field(ge=0)


class ProductUpdate(BaseModel):
    name: str | None = None
    section: str | None = None
    description: str | None = None
    discount: float | None = Field(default=None, ge=0, le=100)
    price: float | None = Field(default=None, ge=0)


class Pagination(BaseModel):
    limit: int
    offset: int
    count: int  # items returned in this page
    total: int  # total items matching the filter (ignoring limit/offset)


class ProductPage(BaseModel):
    items: list[Product]
    pagination: Pagination
