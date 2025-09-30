from sqlalchemy import Boolean, Column, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# Модель для секретного гостя, основная логика программы будет с ней
class ProgramHotel(Base):
    __tablename__ = "program_hotels"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)
    check_in_date = Column(DateTime(timezone=True), nullable=False)
    check_out_date = Column(DateTime(timezone=True), nullable=False)
    slots_total = Column(Integer, nullable=False)
    slots_available = Column(Integer, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    hotel = relationship("Hotel", back_populates="program_entries")