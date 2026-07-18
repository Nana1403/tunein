from uuid import uuid4

from models import Playlist
from .storage_service import StorageService


class PlaylistService:
    def __init__(self, storage: StorageService) -> None:
        self.storage = storage
        self.playlists = [Playlist.model_validate(item) for item in storage.load("playlists.json", [])]

    def _save(self) -> None:
        self.storage.save("playlists.json", [item.model_dump(mode="json") for item in self.playlists])

    def create(self, name: str, description: str = "") -> Playlist:
        playlist = Playlist(id=uuid4().hex[:10], name=name.strip(), description=description.strip())
        self.playlists.append(playlist)
        self._save()
        return playlist

    def delete(self, playlist_id: str) -> None:
        self.playlists = [item for item in self.playlists if item.id != playlist_id]
        self._save()

    def add_song(self, playlist_id: str, song_id: str) -> None:
        playlist = next(item for item in self.playlists if item.id == playlist_id)
        if song_id not in playlist.song_ids:
            playlist.song_ids.append(song_id)
            self._save()

    def remove_song(self, playlist_id: str, song_id: str) -> None:
        playlist = next(item for item in self.playlists if item.id == playlist_id)
        playlist.song_ids = [item for item in playlist.song_ids if item != song_id]
        self._save()
