from app.db.base_class import Base
from app.models.user import User
from app.models.hotel import Hotel
from app.models.program_application import ProgramApplication
from app.models.program_hotel import ProgramHotel

__all__ = ["Base", "User", "ProgramApplication", "Hotel", "ProgramHotel", "Promocode","Inspection","Report",]
