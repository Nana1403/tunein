from models import Song, SongRating, UserProfile
from services.recommender import recommend, score_song


def song(**changes):
    values = dict(id="one", title="One", artist="Artist", genre="Pop", mood="Happy", energy=.8, tempo=120, valence=.8, danceability=.8, acousticness=.1)
    values.update(changes)
    return Song(**values)


def test_exact_genre_and_mood_match_beats_non_match():
    profile = UserProfile(favorite_genre="Pop", favorite_mood="Happy", target_energy=.8)
    exact = song(id="exact")
    different = song(id="different", genre="Jazz", mood="Calm")
    assert score_song(exact, profile).score > score_song(different, profile).score


def test_feedback_changes_score():
    profile = UserProfile()
    track = song()
    liked = score_song(track, profile, SongRating(song_id=track.id, status="liked")).score
    disliked = score_song(track, profile, SongRating(song_id=track.id, status="disliked")).score
    assert liked - disliked == 40


def test_recommend_honors_limit_and_sort_order():
    profile = UserProfile(favorite_genre="Pop", favorite_mood="Happy")
    songs = [song(id="a"), song(id="b", energy=.1), song(id="c", genre="Rock")]
    result = recommend(songs, profile, {}, limit=2)
    assert len(result) == 2
    assert result[0].score >= result[1].score
