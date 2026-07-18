from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import webbrowser

from models import SongRating, UserProfile
from services.music_library import MusicLibrary
from services.playlist_service import PlaylistService
from services.recommender import recommend
from services.report_generator import generate_report
from services.storage_service import StorageService


ROOT = Path(__file__).resolve().parents[1]
PURPLE = "#6D28D9"
INK = "#201A2B"
MUTED = "#746D80"
PAPER = "#F7F4FC"


class TuneInApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("TuneIn — Music Discovery")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(bg=PAPER)

        self.storage = StorageService(ROOT / "data")
        self.library = MusicLibrary(self.storage)
        self.playlist_service = PlaylistService(self.storage)
        self.profile = UserProfile.model_validate(self.storage.load("user_profile.json", {}))
        self.ratings = {
            item["song_id"]: SongRating.model_validate(item)
            for item in self.storage.load("ratings.json", [])
        }
        self.history = self.storage.load("history.json", [])
        self.recommendations = []
        self._configure_style()
        self._build_header()
        self._build_tabs()
        self.refresh_all()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=PAPER)
        style.configure("Card.TFrame", background="white")
        style.configure("TLabel", background=PAPER, foreground=INK, font=("Helvetica", 11))
        style.configure("Title.TLabel", font=("Helvetica", 27, "bold"), foreground=INK)
        style.configure("Subtitle.TLabel", foreground=MUTED)
        style.configure("Card.TLabel", background="white", foreground=INK)
        style.configure("Accent.TButton", background=PURPLE, foreground="white", padding=(16, 10), font=("Helvetica", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#7C3AED")])
        style.configure("TButton", padding=(12, 8))
        style.configure("Treeview", rowheight=32, font=("Helvetica", 10), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), padding=8)
        style.configure("TNotebook", background=PAPER, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(15, 10), font=("Helvetica", 10))
        style.map("TNotebook.Tab", foreground=[("selected", PURPLE)], background=[("selected", "white")])

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=INK, height=88)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="♫", bg=INK, fg="#C4B5FD", font=("Helvetica", 30, "bold")).pack(side="left", padx=(28, 8))
        tk.Label(header, text="TuneIn", bg=INK, fg="white", font=("Helvetica", 24, "bold")).pack(side="left")
        tk.Label(header, text="Your taste. Your soundtrack.", bg=INK, fg="#BDB5C8", font=("Helvetica", 11)).pack(side="left", padx=18)
        ttk.Button(header, text="Export profile report", style="Accent.TButton", command=self.export_report).pack(side="right", padx=28, pady=20)

    def _build_tabs(self) -> None:
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=22, pady=(18, 22))
        builders = [
            ("Home", self._home_tab), ("Discover", self._discover_tab), ("Library", self._library_tab),
            ("Playlists", self._playlists_tab), ("Favorites", self._favorites_tab),
            ("Statistics", self._statistics_tab), ("Profile", self._profile_tab),
        ]
        for label, builder in builders:
            frame = ttk.Frame(self.tabs, padding=16)
            self.tabs.add(frame, text=label)
            builder(frame)

    def _heading(self, parent, title: str, subtitle: str) -> None:
        ttk.Label(parent, text=title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(parent, text=subtitle, style="Subtitle.TLabel").pack(anchor="w", pady=(2, 16))

    def _make_tree(self, parent, columns, widths=None) -> ttk.Treeview:
        tree = ttk.Treeview(parent, columns=[item[0] for item in columns], show="headings", selectmode="browse")
        for index, (key, label) in enumerate(columns):
            tree.heading(key, text=label)
            tree.column(key, width=(widths or {}).get(key, 130), anchor="w")
        tree.pack(fill="both", expand=True)
        return tree

    def _home_tab(self, frame) -> None:
        self._heading(frame, f"Welcome back, {self.profile.name}", "Fresh matches from your listening profile")
        self.home_tree = self._make_tree(frame, [("title", "Track"), ("artist", "Artist"), ("match", "Match"), ("why", "Why it fits")], {"title": 240, "artist": 180, "match": 90, "why": 360})
        actions = ttk.Frame(frame)
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="Mark as listened", command=lambda: self.mark_listened(self.home_tree)).pack(side="left")
        ttk.Button(actions, text="Like", command=lambda: self.set_status(self.home_tree, "liked")).pack(side="left", padx=8)
        ttk.Button(actions, text="Add to playlist", command=lambda: self.add_selected_to_playlist(self.home_tree)).pack(side="left")

    def _discover_tab(self, frame) -> None:
        self._heading(frame, "Discover your next favorite", "Tune the controls and generate a new set of matches")
        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=(0, 12))
        self.discover_genre = tk.StringVar(value=self.profile.favorite_genre)
        self.discover_mood = tk.StringVar(value=self.profile.favorite_mood)
        self.discover_energy = tk.DoubleVar(value=self.profile.target_energy)
        self.discover_tempo = tk.IntVar(value=self.profile.preferred_tempo)
        for label, variable, values in [
            ("Genre", self.discover_genre, ["Any", *self.library.genres]),
            ("Mood", self.discover_mood, ["Any", *self.library.moods]),
        ]:
            box = ttk.Frame(controls)
            box.pack(side="left", padx=(0, 14))
            ttk.Label(box, text=label).pack(anchor="w")
            ttk.Combobox(box, textvariable=variable, values=values, state="readonly", width=16).pack()
        ttk.Label(controls, text="Energy").pack(side="left", padx=(6, 4))
        ttk.Scale(controls, from_=0, to=1, variable=self.discover_energy, length=150).pack(side="left")
        ttk.Label(controls, text="Tempo").pack(side="left", padx=(16, 4))
        ttk.Spinbox(controls, from_=40, to=240, textvariable=self.discover_tempo, width=6).pack(side="left")
        ttk.Button(controls, text="Find matches", style="Accent.TButton", command=self.run_discovery).pack(side="right")
        self.discover_tree = self._make_tree(frame, [("title", "Track"), ("artist", "Artist"), ("genre", "Genre"), ("mood", "Mood"), ("match", "Score"), ("why", "Match notes")], {"title": 210, "artist": 160, "why": 290})
        actions = ttk.Frame(frame); actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="Mark as listened", command=lambda: self.mark_listened(self.discover_tree)).pack(side="left")
        ttk.Button(actions, text="Rate", command=lambda: self.rate_selected(self.discover_tree)).pack(side="left", padx=8)
        ttk.Button(actions, text="Like", command=lambda: self.set_status(self.discover_tree, "liked")).pack(side="left")
        ttk.Button(actions, text="Dislike", command=lambda: self.set_status(self.discover_tree, "disliked")).pack(side="left", padx=8)
        ttk.Button(actions, text="Add to playlist", command=lambda: self.add_selected_to_playlist(self.discover_tree)).pack(side="left")

    def _library_tab(self, frame) -> None:
        self._heading(frame, "Music library", "Search and filter the local catalog")
        filters = ttk.Frame(frame); filters.pack(fill="x", pady=(0, 12))
        self.search_var = tk.StringVar(); self.genre_filter = tk.StringVar(value="Any"); self.mood_filter = tk.StringVar(value="Any")
        search = ttk.Entry(filters, textvariable=self.search_var, width=34); search.pack(side="left"); search.bind("<KeyRelease>", lambda _event: self.refresh_library())
        for variable, values in [(self.genre_filter, ["Any", *self.library.genres]), (self.mood_filter, ["Any", *self.library.moods])]:
            combo = ttk.Combobox(filters, textvariable=variable, values=values, state="readonly", width=15); combo.pack(side="left", padx=(10, 0)); combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_library())
        self.library_tree = self._make_tree(frame, [("title", "Track"), ("artist", "Artist"), ("genre", "Genre"), ("mood", "Mood"), ("energy", "Energy"), ("tempo", "BPM"), ("rating", "Rating")], {"title": 220, "artist": 160})
        actions = ttk.Frame(frame); actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="Mark as listened", command=lambda: self.mark_listened(self.library_tree)).pack(side="left")
        ttk.Button(actions, text="Rate", command=lambda: self.rate_selected(self.library_tree)).pack(side="left", padx=8)
        ttk.Button(actions, text="Like", command=lambda: self.set_status(self.library_tree, "liked")).pack(side="left")
        ttk.Button(actions, text="Add to playlist", command=lambda: self.add_selected_to_playlist(self.library_tree)).pack(side="left", padx=8)

    def _playlists_tab(self, frame) -> None:
        self._heading(frame, "Your playlists", "Build collections for every part of your day")
        panes = ttk.Panedwindow(frame, orient="horizontal"); panes.pack(fill="both", expand=True)
        left = ttk.Frame(panes, padding=(0, 0, 10, 0)); right = ttk.Frame(panes, padding=(10, 0, 0, 0)); panes.add(left, weight=1); panes.add(right, weight=3)
        self.playlist_list = tk.Listbox(left, borderwidth=0, font=("Helvetica", 12), activestyle="none", exportselection=False)
        self.playlist_list.pack(fill="both", expand=True); self.playlist_list.bind("<<ListboxSelect>>", lambda _event: self.refresh_playlist_songs())
        row = ttk.Frame(left); row.pack(fill="x", pady=(10, 0))
        ttk.Button(row, text="New", command=self.create_playlist).pack(side="left")
        ttk.Button(row, text="Delete", command=self.delete_playlist).pack(side="left", padx=6)
        self.playlist_song_tree = self._make_tree(right, [("title", "Track"), ("artist", "Artist"), ("genre", "Genre"), ("mood", "Mood")], {"title": 240, "artist": 180})
        ttk.Button(right, text="Remove selected song", command=self.remove_playlist_song).pack(anchor="w", pady=(10, 0))

    def _favorites_tab(self, frame) -> None:
        self._heading(frame, "Favorites", "Liked songs and tracks rated four stars or higher")
        self.favorite_tree = self._make_tree(frame, [("title", "Track"), ("artist", "Artist"), ("genre", "Genre"), ("mood", "Mood"), ("rating", "Rating"), ("status", "Status")], {"title": 240, "artist": 180})
        ttk.Button(frame, text="Remove like", command=lambda: self.set_status(self.favorite_tree, "neutral")).pack(anchor="w", pady=(10, 0))

    def _statistics_tab(self, frame) -> None:
        self._heading(frame, "Listening statistics", "A simple snapshot of your TuneIn activity")
        self.stats_container = ttk.Frame(frame); self.stats_container.pack(fill="both", expand=True)

    def _profile_tab(self, frame) -> None:
        self._heading(frame, "Listening profile", "These preferences power your recommendations")
        card = ttk.Frame(frame, style="Card.TFrame", padding=28); card.pack(anchor="w", fill="x")
        self.profile_name = tk.StringVar(value=self.profile.name); self.profile_genre = tk.StringVar(value=self.profile.favorite_genre); self.profile_mood = tk.StringVar(value=self.profile.favorite_mood)
        self.profile_energy = tk.DoubleVar(value=self.profile.target_energy); self.profile_tempo = tk.IntVar(value=self.profile.preferred_tempo)
        self.profile_acoustic = tk.BooleanVar(value=self.profile.prefers_acoustic); self.profile_dance = tk.BooleanVar(value=self.profile.prefers_danceable)
        fields = [("Your name", ttk.Entry(card, textvariable=self.profile_name, width=34)), ("Favorite genre", ttk.Combobox(card, textvariable=self.profile_genre, values=["Any", *self.library.genres], state="readonly", width=31)), ("Favorite mood", ttk.Combobox(card, textvariable=self.profile_mood, values=["Any", *self.library.moods], state="readonly", width=31)), ("Preferred tempo", ttk.Spinbox(card, from_=40, to=240, textvariable=self.profile_tempo, width=32))]
        for index, (label, widget) in enumerate(fields):
            ttk.Label(card, text=label, style="Card.TLabel").grid(row=index, column=0, sticky="w", padx=(0, 18), pady=7); widget.grid(row=index, column=1, sticky="w", pady=7)
        ttk.Label(card, text="Target energy", style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=7); ttk.Scale(card, from_=0, to=1, variable=self.profile_energy, length=250).grid(row=4, column=1, sticky="w")
        ttk.Checkbutton(card, text="Prefer acoustic tracks", variable=self.profile_acoustic).grid(row=5, column=1, sticky="w", pady=6)
        ttk.Checkbutton(card, text="Prefer danceable tracks", variable=self.profile_dance).grid(row=6, column=1, sticky="w", pady=6)
        ttk.Button(card, text="Save profile", style="Accent.TButton", command=self.save_profile).grid(row=7, column=1, sticky="w", pady=(18, 0))

    def refresh_all(self) -> None:
        self.recommendations = recommend(self.library.songs, self.profile, self.ratings, 12)
        self.refresh_home(); self.refresh_discover(); self.refresh_library(); self.refresh_playlists(); self.refresh_favorites(); self.refresh_stats()

    @staticmethod
    def _clear(tree) -> None:
        tree.delete(*tree.get_children())

    def refresh_home(self) -> None:
        self._clear(self.home_tree)
        for item in self.recommendations[:8]:
            self.home_tree.insert("", "end", iid=item.song.id, values=(item.song.title, item.song.artist, f"{item.score:.0f}", ", ".join(item.reasons) or "overall fit"))

    def run_discovery(self) -> None:
        try:
            temp = self.profile.model_copy(update={"favorite_genre": self.discover_genre.get(), "favorite_mood": self.discover_mood.get(), "target_energy": self.discover_energy.get(), "preferred_tempo": self.discover_tempo.get()})
            self.recommendations = recommend(self.library.songs, temp, self.ratings, 12)
            self.refresh_discover()
        except ValueError as exc:
            messagebox.showerror("Check your preferences", str(exc))

    def refresh_discover(self) -> None:
        self._clear(self.discover_tree)
        for item in self.recommendations:
            song = item.song
            self.discover_tree.insert("", "end", iid=song.id, values=(song.title, song.artist, song.genre, song.mood, f"{item.score:.0f}", ", ".join(item.reasons) or "overall fit"))

    def refresh_library(self) -> None:
        self._clear(self.library_tree)
        for song in self.library.search(self.search_var.get(), self.genre_filter.get(), self.mood_filter.get()):
            rating = self.ratings.get(song.id)
            self.library_tree.insert("", "end", iid=song.id, values=(song.title, song.artist, song.genre, song.mood, f"{song.energy:.0%}", song.tempo, "★" * rating.rating if rating else "—"))

    def refresh_playlists(self) -> None:
        selected = self.playlist_list.curselection()
        index = selected[0] if selected else 0
        self.playlist_list.delete(0, "end")
        for playlist in self.playlist_service.playlists:
            self.playlist_list.insert("end", f"{playlist.name}  ·  {len(playlist.song_ids)}")
        if self.playlist_service.playlists:
            self.playlist_list.selection_set(min(index, len(self.playlist_service.playlists) - 1))
        self.refresh_playlist_songs()

    def refresh_playlist_songs(self) -> None:
        self._clear(self.playlist_song_tree)
        selected = self.playlist_list.curselection()
        if not selected: return
        playlist = self.playlist_service.playlists[selected[0]]
        for song_id in playlist.song_ids:
            song = self.library.get(song_id)
            if song: self.playlist_song_tree.insert("", "end", iid=song.id, values=(song.title, song.artist, song.genre, song.mood))

    def refresh_favorites(self) -> None:
        self._clear(self.favorite_tree)
        for song in self.library.songs:
            rating = self.ratings.get(song.id)
            if rating and (rating.status == "liked" or rating.rating >= 4):
                self.favorite_tree.insert("", "end", iid=song.id, values=(song.title, song.artist, song.genre, song.mood, "★" * rating.rating or "—", rating.status.title()))

    def refresh_stats(self) -> None:
        for child in self.stats_container.winfo_children(): child.destroy()
        played = [self.library.get(item.get("song_id", "")) for item in self.history]
        played = [song for song in played if song]
        genre_counts = Counter(song.genre for song in played); artist_counts = Counter(song.artist for song in played); mood_counts = Counter(song.mood for song in played)
        liked = sum(1 for rating in self.ratings.values() if rating.status == "liked")
        average_energy = sum(song.energy for song in played) / len(played) if played else 0
        metrics = [("Recently played", len(self.history)), ("Liked songs", liked), ("Playlists", len(self.playlist_service.playlists)), ("Average energy", f"{average_energy:.0%}"), ("Top genre", genre_counts.most_common(1)[0][0] if genre_counts else "Not enough data"), ("Favorite artist", artist_counts.most_common(1)[0][0] if artist_counts else "Not enough data"), ("Common mood", mood_counts.most_common(1)[0][0] if mood_counts else "Not enough data")]
        for index, (label, value) in enumerate(metrics):
            card = ttk.Frame(self.stats_container, style="Card.TFrame", padding=22); card.grid(row=index // 4, column=index % 4, sticky="nsew", padx=7, pady=7)
            ttk.Label(card, text=str(value), style="Card.TLabel", font=("Helvetica", 20, "bold"), foreground=PURPLE).pack(anchor="w"); ttk.Label(card, text=label, style="Card.TLabel").pack(anchor="w", pady=(5, 0))
        for col in range(4): self.stats_container.columnconfigure(col, weight=1)

    def selected_song_id(self, tree) -> str | None:
        selected = tree.selection()
        if not selected: messagebox.showinfo("Select a song", "Choose a song first."); return None
        return selected[0]

    def _save_ratings(self) -> None:
        self.storage.save("ratings.json", [rating.model_dump(mode="json") for rating in self.ratings.values()])

    def set_status(self, tree, status: str) -> None:
        song_id = self.selected_song_id(tree)
        if not song_id: return
        current = self.ratings.get(song_id, SongRating(song_id=song_id))
        self.ratings[song_id] = current.model_copy(update={"status": status})
        self._save_ratings(); self.refresh_all()

    def rate_selected(self, tree) -> None:
        song_id = self.selected_song_id(tree)
        if not song_id: return
        value = simpledialog.askinteger("Rate song", "Rating from 1 to 5:", minvalue=1, maxvalue=5, parent=self)
        if value is None: return
        current = self.ratings.get(song_id, SongRating(song_id=song_id))
        self.ratings[song_id] = current.model_copy(update={"rating": value})
        self._save_ratings(); self.refresh_all()

    def mark_listened(self, tree) -> None:
        song_id = self.selected_song_id(tree)
        if not song_id: return
        self.history.insert(0, {"song_id": song_id, "selected_at": datetime.now(timezone.utc).isoformat()})
        self.history = self.history[:100]; self.storage.save("history.json", self.history); self.refresh_stats()
        song = self.library.get(song_id); messagebox.showinfo("Added to history", f"{song.title} by {song.artist} was added to your listening history.")

    def create_playlist(self) -> None:
        name = simpledialog.askstring("New playlist", "Playlist name:", parent=self)
        if not name or not name.strip(): return
        try: self.playlist_service.create(name)
        except ValueError as exc: messagebox.showerror("Invalid playlist", str(exc)); return
        self.refresh_playlists(); self.refresh_stats()

    def delete_playlist(self) -> None:
        selected = self.playlist_list.curselection()
        if not selected: return
        playlist = self.playlist_service.playlists[selected[0]]
        if messagebox.askyesno("Delete playlist", f"Delete {playlist.name}?"):
            self.playlist_service.delete(playlist.id); self.refresh_playlists(); self.refresh_stats()

    def add_selected_to_playlist(self, tree) -> None:
        song_id = self.selected_song_id(tree)
        if not song_id: return
        if not self.playlist_service.playlists: messagebox.showinfo("Create a playlist", "Create a playlist in the Playlists tab first."); return
        names = "\n".join(f"{index + 1}. {item.name}" for index, item in enumerate(self.playlist_service.playlists))
        number = simpledialog.askinteger("Add to playlist", f"Choose a playlist number:\n\n{names}", minvalue=1, maxvalue=len(self.playlist_service.playlists), parent=self)
        if number is None: return
        self.playlist_service.add_song(self.playlist_service.playlists[number - 1].id, song_id); self.refresh_playlists(); self.refresh_stats()

    def remove_playlist_song(self) -> None:
        selected_playlist = self.playlist_list.curselection(); song_id = self.selected_song_id(self.playlist_song_tree)
        if not selected_playlist or not song_id: return
        self.playlist_service.remove_song(self.playlist_service.playlists[selected_playlist[0]].id, song_id); self.refresh_playlists()

    def save_profile(self) -> None:
        try:
            self.profile = UserProfile(name=self.profile_name.get(), favorite_genre=self.profile_genre.get(), favorite_mood=self.profile_mood.get(), target_energy=self.profile_energy.get(), preferred_tempo=self.profile_tempo.get(), prefers_acoustic=self.profile_acoustic.get(), prefers_danceable=self.profile_dance.get())
        except ValueError as exc: messagebox.showerror("Check your profile", str(exc)); return
        self.storage.save("user_profile.json", self.profile.model_dump(mode="json")); self.discover_genre.set(self.profile.favorite_genre); self.discover_mood.set(self.profile.favorite_mood); self.discover_energy.set(self.profile.target_energy); self.discover_tempo.set(self.profile.preferred_tempo); self.refresh_all(); messagebox.showinfo("Profile saved", "Your recommendations have been refreshed.")

    def export_report(self) -> None:
        path = generate_report(ROOT / "reports" / "music_profile.html", self.profile, self.library.songs, self.ratings, self.playlist_service.playlists, self.recommendations)
        webbrowser.open(path.as_uri())
        messagebox.showinfo("Report created", f"Your report was saved to:\n{path}")
