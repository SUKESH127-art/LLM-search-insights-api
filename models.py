# models.py

import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import String, DateTime, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base
from schemas import StatusEnum # This import will still be resolved in the next step

# Load CACHE_TTL_HOURS from .env
import os
from dotenv import load_dotenv

load_dotenv()
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", 24))

def get_expiration_time():
    return datetime.now(timezone.utc) + timedelta(hours=CACHE_TTL_HOURS)

class Analysis(Base):
    __tablename__ = "analyses"

    # Switched to Mapped and mapped_column for modern, typed declarations
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    research_question: Mapped[str] = mapped_column(String(500))
    
    status: Mapped[str] = mapped_column(String(50), default=StatusEnum.QUEUED)
    progress: Mapped[int] = mapped_column(default=0)
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # The JSON type in SQLAlchemy automatically handles the dictionary-like data
    full_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_expiration_time)