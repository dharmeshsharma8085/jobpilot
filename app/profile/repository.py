
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile_record import ProfileRecord
from app.profile.schemas import ProfileSettings


def get_profile(db: Session) -> ProfileRecord | None:
    return db.scalar(
        select(ProfileRecord).where(ProfileRecord.id == 1)
    )


def save_profile(
    db: Session,
    profile: ProfileSettings,
) -> ProfileRecord:
    record = get_profile(db)
    values = profile.model_dump()

    if record is None:
        record = ProfileRecord(id=1, **values)
        db.add(record)
    else:
        for key, value in values.items():
            setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record
