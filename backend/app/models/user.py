from beanie import Document, Indexed
from pydantic import EmailStr, Field

from app.models.common import TimestampMixin


class User(TimestampMixin, Document):
    clerk_user_id: Indexed(str, unique=True) = Field(..., min_length=1)
    email: EmailStr

    class Settings:
        name = "users"
