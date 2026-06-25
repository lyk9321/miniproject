from sqlalchemy import Column, Integer, Text, Enum, Date, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class TimeOffRequest(Base):
    __tablename__ = "time_off_requests"

    request_id = Column(Integer, primary_key=True, autoincrement=True)
    requester_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    type = Column(Enum("OFF", "VAC", name="time_off_type"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(
        Enum("pending", "approved", "rejected", "canceled", name="time_off_status"),
        nullable=False,
        default="pending",
    )
    admin_comment = Column(Text, nullable=True)
    canceled_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    cancel_reason = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    processed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    requester = relationship("User", foreign_keys=[requester_id])
