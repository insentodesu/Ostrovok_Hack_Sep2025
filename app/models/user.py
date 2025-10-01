from sqlalchemy import Boolean, Column, DateTime, Integer, String, JSON, Date
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base_class import Base
from app.db.types import JSONEncodedList
from sqlalchemy.ext.mutable import MutableList

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(String, default="candidate", nullable=False)
    cities: Mapped[list[str]] = mapped_column(
            MutableList.as_mutable(JSONEncodedList()),
            default=list,
            nullable=False,
        )
    guests = Column(Integer, default=1, nullable=True)
    rating = Column(Integer, default=0, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    phone_verified = Column(Boolean, default=False, nullable=False)
    completed_bookings_last_year = Column(Integer, default=0, nullable=False)
    guru_level = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    applications = relationship("ProgramApplication", back_populates="user")
    reports = relationship("Report", back_populates="user")