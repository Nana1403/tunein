from pydantic import BaseModel, ConfigDict, Field


class Song(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str = Field(min_length=1)
    artist: str = Field(min_length=1)
    genre: str = Field(min_length=1)
    mood: str = Field(min_length=1)
    energy: float = Field(ge=0, le=1)
    tempo: int = Field(ge=40, le=240)
    valence: float = Field(ge=0, le=1)
    danceability: float = Field(ge=0, le=1)
    acousticness: float = Field(ge=0, le=1)
    audio_file: str | None = None
