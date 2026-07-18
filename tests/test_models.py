import pytest
from pydantic import ValidationError

from models import Song, UserProfile


def test_song_rejects_energy_outside_unit_range():
    with pytest.raises(ValidationError):
        Song(id="x", title="Test", artist="Artist", genre="Pop", mood="Happy", energy=1.2, tempo=120, valence=.5, danceability=.5, acousticness=.5)


def test_profile_has_beginner_friendly_defaults():
    profile = UserProfile()
    assert profile.preferred_tempo == 120
    assert 0 <= profile.target_energy <= 1
