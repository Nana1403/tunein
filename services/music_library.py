from models import Song
from .storage_service import StorageService


class MusicLibrary:
    def __init__(self, storage: StorageService) -> None:
        self.storage = storage
        self.songs = [Song.model_validate(item) for item in storage.load("songs.json", [])]

    def get(self, song_id: str) -> Song | None:
        return next((song for song in self.songs if song.id == song_id), None)

    def search(self, query: str = "", genre: str = "Any", mood: str = "Any") -> list[Song]:
        needle = query.strip().lower()
        return [
            song for song in self.songs
            if (not needle or needle in f"{song.title} {song.artist} {song.genre} {song.mood}".lower())
            and (genre == "Any" or song.genre == genre)
            and (mood == "Any" or song.mood == mood)
        ]

    @property
    def genres(self) -> list[str]:
        return sorted({song.genre for song in self.songs})

    @property
    def moods(self) -> list[str]:
        return sorted({song.mood for song in self.songs})
