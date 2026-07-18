from pydantic import BaseModel, ConfigDict, Field


class UserProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="Music Explorer", min_length=1, max_length=60)
    favorite_genre: str = "Any"
    favorite_mood: str = "Any"
    target_energy: float = Field(default=0.7, ge=0, le=1)
    preferred_tempo: int = Field(default=120, ge=40, le=240)
    prefers_acoustic: bool = False
    prefers_danceable: bool = True
