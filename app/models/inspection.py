import enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class InspectionStatus(str, enum.Enum):
    awaiting_booking = "awaiting_booking"
    awaiting_report = "awaiting_report"
    completed = "completed"


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)
    guest_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    promocode_id = Column(Integer, ForeignKey("promocodes.id", ondelete="SET NULL"), nullable=True)
    booking_id = Column(String, nullable=True)
    report_id = Column(
        Integer,
        ForeignKey("reports.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    status = Column(
        SAEnum(InspectionStatus, name="inspectionstatus", native_enum=False),
        default=InspectionStatus.awaiting_booking,
        nullable=False,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    hotel = relationship("Hotel", back_populates="inspections")
    guest = relationship("User", back_populates="inspections")
    promocode = relationship("Promocode", back_populates="inspection")
    report = relationship(
        "Report",
        back_populates="inspection",
        foreign_keys=[report_id],
        cascade="all, delete-orphan",
        single_parent=True,
    )