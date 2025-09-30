from sqlalchemy import Boolean, Column, DateTime, Integer, String, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(String, default="candidate", nullable=False)
    cities = Column(ARRAY[str], nullable=True)
    guests = Column(Integer, default=1, nullable=True)
    rating = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    applications = relationship("ProgramApplication", back_populates="user")
    inspections = relationship("Inspection",back_populates="guest",passive_deletes=True)
