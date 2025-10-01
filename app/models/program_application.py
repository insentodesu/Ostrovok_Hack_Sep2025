import enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class ProgramApplicationStatus(str, enum.Enum):
    draft = "draft"
    in_review = "in_review"
    shortlisted = "shortlisted"
    rejected = "rejected"
    accepted = "accepted"


class ProgramApplication(Base):
    __tablename__ = "program_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    travel_party = Column(String, nullable=False)
    city_home = Column(String, nullable=False)
    city_desired = Column(String, nullable=False)
    answers = Column(JSON, nullable=False)
    review_text = Column(Text, nullable=False)
    photos = Column(JSON, nullable=False, default=list)
    status = Column(
        SAEnum(ProgramApplicationStatus, name="programapplicationstatus", native_enum=False),
        default=ProgramApplicationStatus.draft,
        nullable=False,
    )
    reviewer_comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="applications")
