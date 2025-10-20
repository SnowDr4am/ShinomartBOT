from sqlalchemy import String, TIMESTAMP, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class QRCode(Base):
    __tablename__ = 'qr_codes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    phone_number = mapped_column(String, nullable=False)
    created_at = mapped_column(TIMESTAMP, nullable=False)

    user = relationship("User", back_populates="qr_codes")