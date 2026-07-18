# TuneIn

TuneIn is an offline desktop music discovery app built with Python, Tkinter, and Pydantic. It uses a transparent weighted scoring model to recommend tracks from a local catalog—no account, API key, or internet connection required.

## Features

- Personalized recommendations based on genre, mood, energy, tempo, acousticness, and danceability
- Searchable, filterable 16-song sample catalog
- Likes, dislikes, five-star ratings, and listening history
- Local playlist creation and management
- Listening statistics dashboard
- A styled HTML personal music report
- JSON persistence and Pydantic validation
- Pytest coverage for models, recommendations, and playlists

The included songs are fictional metadata entries. No copyrighted audio ships with the project.

## How TuneIn Works

- The application loads songs from a JSON file.
- The user creates or updates their music profile.
- Pydantic validates the profile information.
- The recommendation system compares the profile with every song.
- Each song receives a recommendation score.
- Songs are sorted from highest to lowest score.
- The best matches are displayed in the Tkinter interface.
- The user can like, rate, preview, or add songs to playlists.
- TuneIn saves the user’s activity locally.
- The user can generate an HTML music profile report.

Recommendation model

- Each song receives up to 30 genre points, 25 mood points, 20 energy-proximity points, 10 tempo-proximity points, and 10 points each for acoustic and danceability fit. A like adds 15, a dislike subtracts 25, and each rating star adds 2. The Discover page shows the leading reasons beside every result.

Add music

- Add a validated song object to `data/songs.json`. Values for `energy`, `valence`, `danceability`, and `acousticness` must be between `0.0` and `1.0`; tempo must be between 40 and 240 BPM. An optional `audio_file` field is reserved for a future preview player. User-created state is stored in the other JSON files under `data/`. Use only your own or copyright-free audio if you extend preview playback.

## Demo Walkthrough

<img src="images/demo.gif" width=500>


## Future Features

- Connect to the Spotify API
- Retrieve album covers
- Search for real artists and songs
- Recommend songs using machine learning
- Create profiles for multiple users
- Add dark and light themes
- Add an AI music assistant

## Run it

Python 3.10 or later is recommended. Tkinter is included with most standard Python installations.

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    python main.py
    ```
On Linux, install your distribution's Tk package if `import tkinter` fails (often `python3-tk`).

## Test it

    ```bash
    pytest -q
    ```

