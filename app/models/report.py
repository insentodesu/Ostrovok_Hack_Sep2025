from sqlalchemy import Column, DateTime, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class Report(Base):
    __tablename__ = "reports"
    #TODO: Images
    id = Column(Integer, primary_key=True, index=True)
    summary = Column(Text, nullable=True)

    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    inspection = relationship("Inspection", back_populates="report", uselist=False)