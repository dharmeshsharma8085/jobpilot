
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProfileRecord(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_roles: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    skills: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    preferred_locations: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    projects: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    preferred_employment_types: Mapped[list] = mapped_column(
        JSONB, default=list, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
