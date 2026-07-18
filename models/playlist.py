from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class Playlist(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=240)
    song_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
