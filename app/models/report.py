import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


REPORT_STATUSES = ("draft", "on_moderation", "approved", "rejected")
PHOTO_SECTIONS = ("photos_match", "cleanliness", "food", "general")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    checkout_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        Enum(*REPORT_STATUSES, name="report_status"),
        nullable=False,
        default="draft",
    )
    answers = Column(JSON, nullable=False, default=dict)
    overall_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    photos = relationship(
        "Photo",
        back_populates="report",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    user = relationship("User", back_populates="reports")
    hotel = relationship("Hotel", back_populates="reports")

    #TODO: В будущем появиться FK на Inspection / Booking


class Photo(Base):
    __tablename__ = "report_photos"
    __table_args__ = (
        CheckConstraint(
            "section IN ('photos_match', 'cleanliness', 'food', 'general')",
            name="ck_report_photos_section",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    section = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    mime = Column(String, nullable=True)
    size = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    report = relationship("Report", back_populates="photos")