from services.playlist_service import PlaylistService
from services.storage_service import StorageService


def test_playlist_round_trip(tmp_path):
    service = PlaylistService(StorageService(tmp_path))
    playlist = service.create("Road Trip")
    service.add_song(playlist.id, "song-1")

    reloaded = PlaylistService(StorageService(tmp_path))
    assert reloaded.playlists[0].name == "Road Trip"
    assert reloaded.playlists[0].song_ids == ["song-1"]
