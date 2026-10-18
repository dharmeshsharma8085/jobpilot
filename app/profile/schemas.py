
from pydantic import BaseModel, Field, field_validator


class ProfileSettings(BaseModel):
    target_roles: list[str] = Field(default_factory=list, max_length=50)
    skills: list[str] = Field(default_factory=list, max_length=200)
    preferred_locations: list[str] = Field(default_factory=list, max_length=50)
    projects: list[str] = Field(default_factory=list, max_length=100)
    preferred_employment_types: list[str] = Field(
        default_factory=lambda: ["Internship"],
        max_length=20,
    )

    @field_validator(
        "target_roles",
        "skills",
        "preferred_locations",
        "projects",
        "preferred_employment_types",
    )
    @classmethod
    def clean_values(cls, values: list[str]) -> list[str]:
        cleaned = []
        seen = set()

        for value in values:
            value = value.strip()
            if not value:
                continue

            key = value.casefold()
            if key not in seen:
                cleaned.append(value)
                seen.add(key)

        return cleaned


class ProfileResponse(ProfileSettings):
    id: int
