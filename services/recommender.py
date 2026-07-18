from dataclasses import dataclass

from models import Song, SongRating, UserProfile


@dataclass(frozen=True)
class Recommendation:
    song: Song
    score: float
    reasons: tuple[str, ...]


def score_song(song: Song, profile: UserProfile, rating: SongRating | None = None) -> Recommendation:
    score = 0.0
    reasons: list[str] = []
    if profile.favorite_genre != "Any" and song.genre == profile.favorite_genre:
        score += 30
        reasons.append("genre match")
    if profile.favorite_mood != "Any" and song.mood == profile.favorite_mood:
        score += 25
        reasons.append("mood match")

    energy_points = max(0.0, 20 * (1 - abs(song.energy - profile.target_energy)))
    tempo_points = max(0.0, 10 * (1 - abs(song.tempo - profile.preferred_tempo) / 100))
    acoustic_target = 1.0 if profile.prefers_acoustic else 0.0
    dance_target = 1.0 if profile.prefers_danceable else 0.0
    acoustic_points = 10 * (1 - abs(song.acousticness - acoustic_target))
    dance_points = 10 * (1 - abs(song.danceability - dance_target))
    score += energy_points + tempo_points + acoustic_points + dance_points
    if energy_points >= 16:
        reasons.append("energy fit")
    if tempo_points >= 8:
        reasons.append("tempo fit")
    if acoustic_points >= 7:
        reasons.append("acoustic fit")
    if dance_points >= 7:
        reasons.append("danceability fit")

    if rating:
        if rating.status == "liked":
            score += 15
            reasons.append("you liked this")
        elif rating.status == "disliked":
            score -= 25
        score += rating.rating * 2

    return Recommendation(song=song, score=round(score, 1), reasons=tuple(reasons[:3]))


def recommend(songs: list[Song], profile: UserProfile, ratings: dict[str, SongRating], limit: int = 10) -> list[Recommendation]:
    ranked = [score_song(song, profile, ratings.get(song.id)) for song in songs]
    return sorted(ranked, key=lambda item: (-item.score, item.song.title))[:limit]
