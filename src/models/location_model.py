from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy import ForeignKey

from src.database import Base


class CountryModel(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    name: Mapped[str] = mapped_column()

    city: Mapped["CityModel"] = relationship(back_populates="country")

    async def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }


class CityModel(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    country_id: Mapped[int] = mapped_column(
        ForeignKey(
            "countries.id",
            ondelete="CASCADE",
        )
    )
    name: Mapped[str] = mapped_column()

    country: Mapped["CountryModel"] = relationship(back_populates="city")

    async def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }
