import enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class ProgramApplicationStatus(str, enum.Enum):
    applied = "applied"
    in_review = "in_review"
    shortlisted = "shortlisted"
    rejected = "rejected"
    accepted = "accepted"


class ProgramApplication(Base):
    __tablename__ = "program_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    email = Column(String, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    city = Column(String, nullable=True)
    motivation = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    status = Column(
        SAEnum(ProgramApplicationStatus, name="programapplicationstatus", native_enum=False),
        default=ProgramApplicationStatus.applied,
        nullable=False,
    )
    reviewer_comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="applications")
