import uuid
from datetime import datetime
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy import ForeignKey
from src.database import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4,
        primary_key=True,
        unique=True,
        index=True,
    )
    auth_type: Mapped[str] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(unique=True)
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)
    about: Mapped[str] = mapped_column(nullable=True)
    avatar: Mapped[str] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(nullable=True)
    birth_date: Mapped[datetime] = mapped_column(default=datetime.now())
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now())
    is_activate: Mapped[bool] = mapped_column(default=False)
    is_locked: Mapped[bool] = mapped_column(default=False)
    role_id: Mapped[int] = mapped_column(
        ForeignKey(
            "roles.id",
            ondelete="CASCADE",
        ),
        default=2,
    )

    hash_password: Mapped[str] = mapped_column(nullable=True)

    role: Mapped["RoleModel"] = relationship(back_populates="user")

    token: Mapped["TokenModel"] = relationship(back_populates="user")
    address: Mapped["AddressModel"] = relationship(back_populates="user")

####################################################################################################
    async def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "about": self.about,
            "avatar": self.avatar,
            "phone": self.phone,
            "birth_date": self.birth_date,
            "created_at": self.created_at,
            "update_at": self.updated_at,
            "is_activate": self.is_activate,
            "is_locked": self.is_locked,
            "hash_password": self.hash_password,
        }
####################################################################################################

class AddressModel(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        unique=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        )
    )
    address_line: Mapped[str] = mapped_column()
    city: Mapped[str] = mapped_column()  # Warning
    state: Mapped[str] = mapped_column()
    postal_code: Mapped[str] = mapped_column()
    country: Mapped[str] = mapped_column()  # Warning
    is_default: Mapped[bool] = mapped_column(default=False)

    user: Mapped["UserModel"] = relationship(back_populates="address")

    async def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "address_line": self.address_line,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
            "is_default": self.is_default,
        }


class TokenModel(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        unique=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    refresh_token: Mapped[str] = mapped_column(unique=True)
    expires_at: Mapped[datetime] = mapped_column()
    user_agent: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())

    user: Mapped["UserModel"] = relationship(back_populates="token")

    async def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "user_agent": self.user_agent,
            "created_at": self.created_at,
        }


class RoleModel(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        unique=True,
        index=True,
    )
    role: Mapped[str] = mapped_column()

    user: Mapped["UserModel"] = relationship(back_populates="role")

    async def to_dict(self):
        pass
