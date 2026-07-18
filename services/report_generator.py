from collections import Counter
from html import escape
from pathlib import Path

from models import Playlist, Song, SongRating, UserProfile
from .recommender import Recommendation


def generate_report(
    output: str | Path,
    profile: UserProfile,
    songs: list[Song],
    ratings: dict[str, SongRating],
    playlists: list[Playlist],
    recommendations: list[Recommendation],
) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    liked = [song for song in songs if ratings.get(song.id) and ratings[song.id].status == "liked"]
    genres = Counter(song.genre for song in liked)
    favorite = genres.most_common(1)[0][0] if genres else profile.favorite_genre
    cards = "".join(
        f'<article class="song"><span>{item.score:.0f}% match</span><h3>{escape(item.song.title)}</h3>'
        f'<p>{escape(item.song.artist)} · {escape(item.song.genre)} · {escape(item.song.mood)}</p></article>'
        for item in recommendations[:6]
    )
    playlist_rows = "".join(
        f"<li><strong>{escape(item.name)}</strong> — {len(item.song_ids)} songs</li>" for item in playlists
    ) or "<li>No playlists yet</li>"
    html = f"""
<!doctype html>
<html lang="en">

<head>
    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width,initial-scale=1"
    >

    <title>
        {escape(profile.name)} · TuneIn Report
    </title>

    <style>
        :root {{
            --ink: #171321;
            --muted: #746d80;
            --accent: #7c3aed;
            --pink: #ec4899;
            --paper: #f7f4ff;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font: 16px/1.55 system-ui;
            color: var(--ink);
            background: var(--paper);
        }}

        main {{
            max-width: 980px;
            margin: auto;
            padding: 64px 24px;
        }}

        header {{
            padding: 48px;
            border-radius: 28px;
            color: white;
            background: linear-gradient(
                135deg,
                var(--accent),
                var(--pink)
            );
        }}

        h1 {{
            font-size: clamp(2.4rem, 7vw, 5rem);
            margin: 0;
        }}

        header p {{
            font-size: 1.25rem;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(
                auto-fit,
                minmax(230px, 1fr)
            );
            gap: 18px;
            margin: 28px 0;
        }}

        .song,
        .panel {{
            background: white;
            border-radius: 18px;
            padding: 22px;
            box-shadow: 0 8px 30px #32145a12;
        }}

        .song span {{
            color: var(--accent);
            font-weight: 800;
        }}

        h2 {{
            margin-top: 44px;
        }}

        h3 {{
            margin-bottom: 4px;
        }}

        .song p {{
            color: var(--muted);
            margin: 0;
        }}

        li {{
            margin: 0.6rem 0;
        }}
    </style>
</head>

<body>

    <main>

        <header>
            <small>
                TUNEIN · PERSONAL LISTENING REPORT
            </small>

            <h1>
                {escape(profile.name)}
            </h1>

            <p>
                Your current sound:
                {escape(favorite)}
                ·
                {escape(profile.favorite_mood)}
                ·
                {profile.target_energy:.0%} energy
            </p>
        </header>

        <h2>
            Made for you
        </h2>

        <section class="grid">
            {cards}
        </section>

        <section class="panel">
            <h2>
                Your library
            </h2>

            <p>
                {len(liked)} liked songs ·
                {len(playlists)} playlists ·
                {len(ratings)} rated or reviewed
            </p>

            <ul>
                {playlist_rows}
            </ul>
        </section>

    </main>

</body>

</html>
"""

    output.write_text(html, encoding="utf-8")
    return output.resolve()

