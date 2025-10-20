from sqlalchemy import TIMESTAMP, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class VoteHistory(Base):
    __tablename__ = 'vote_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    data = mapped_column(TIMESTAMP, nullable=False)

    user = relationship("User", back_populates='vote_history')