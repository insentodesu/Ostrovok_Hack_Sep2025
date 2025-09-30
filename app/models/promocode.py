from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    Numeric,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class Promocode(Base):
    __tablename__ = "promocodes"
    __table_args__ = (
        CheckConstraint(
            "discount BETWEEN 0 AND 1",
            name="ck_promocodes_discount_fraction_range",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    discount = Column(Numeric(3, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    inspection = relationship("Inspection", back_populates="promocode")