from pydantic import BaseModel, ConfigDict, Field


class SongRating(BaseModel):
    model_config = ConfigDict(extra="forbid")

    song_id: str
    rating: int = Field(default=0, ge=0, le=5)
    status: str = Field(default="neutral", pattern="^(liked|disliked|neutral)$")
    comment: str = Field(default="", max_length=300)
