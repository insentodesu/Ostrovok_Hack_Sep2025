from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# Базовая модель отеля(которая якобы уже есть в островке), для вывода информации об отеле
class Hotel(Base):
    __tablename__ = "hotels"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 0 AND 5", name="ck_hotels_rating_range"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    address = Column(String, nullable=False)
    rating = Column(Integer, default=0, nullable=False)
    cost = Column(Integer, nullable=False)
    guests = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    program_entries = relationship(
        "ProgramHotel",
        back_populates="hotel",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    inspections = relationship(
        "Inspection",
        back_populates="hotel",
        passive_deletes=True,
    )