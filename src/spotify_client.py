import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_SCOPES,
    SPOTIFY_BATCH_DELETE,
    SPOTIFY_BATCH_ADD,
)

MAX_RETRY_AFTER = 30


class SpotifyClient:

    def __init__(self):
        auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=SPOTIFY_SCOPES,
        )
        retry = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503],
                       respect_retry_after_header=True)
        adapter = HTTPAdapter(max_retries=retry)
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        self.sp._session.mount("https://", adapter)
        self.sp._session.mount("http://", adapter)

    def get_username(self):
        return self.sp.current_user()["display_name"]

    def get_user_id(self):
        return self.sp.current_user()["id"]

    def remove_all_liked_songs(self):
        total_removed = 0
        while True:
            results = self.sp.current_user_saved_tracks(limit=SPOTIFY_BATCH_DELETE)
            tracks = results.get("items", [])
            if not tracks:
                break
            track_ids = [t["track"]["id"] for t in tracks]
            self.sp.current_user_saved_tracks_delete(tracks=track_ids)
            total_removed += len(track_ids)
            print(f"  Removidas {total_removed} musicas...")
        return total_removed

    def search_track(self, name, artist):
        query = f"track:{name} artist:{artist}"
        result = self._search(query)
        if result and result != "RATE_LIMITED":
            return result
        if result == "RATE_LIMITED":
            return result
        time.sleep(0.5)
        return self._search(f"{name} {artist}")

    def get_my_playlists(self):
        playlists = []
        results = self.sp.current_user_playlists(limit=50)
        while results:
            for item in results["items"]:
                playlists.append({
                    "id": item["id"],
                    "name": item["name"],
                    "total": item.get("tracks", {}).get("total", 0),
                    "url": item.get("external_urls", {}).get("spotify", ""),
                })
            if results["next"]:
                results = self.sp.next(results)
            else:
                break
        return playlists

    def add_to_playlist(self, playlist_id, track_uris):
        for i in range(0, len(track_uris), SPOTIFY_BATCH_ADD):
            batch = track_uris[i:i + SPOTIFY_BATCH_ADD]
            self.sp.playlist_add_items(playlist_id, batch)

    def create_playlist(self, name, track_uris, cover_base64=None):
        payload = {"name": name, "public": False, "description": "Criada pelo SpotifyBot"}
        response = self.sp._post("me/playlists", payload=payload)
        playlist_id = response["id"]
        if cover_base64:
            try:
                self.sp.playlist_upload_cover_image(playlist_id, cover_base64)
            except Exception:
                print("  Aviso: nao foi possivel definir a capa da playlist.")
        for i in range(0, len(track_uris), SPOTIFY_BATCH_ADD):
            batch = track_uris[i:i + SPOTIFY_BATCH_ADD]
            self.sp.playlist_add_items(playlist_id, batch)
        return response["external_urls"]["spotify"]

    def _search(self, query):
        try:
            results = self.sp.search(q=query, type="track", limit=1)
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                print("  [!] Rate limit do Spotify atingido. Aguarde alguns minutos e tente novamente.")
                return "RATE_LIMITED"
            raise
        items = results.get("tracks", {}).get("items", [])
        if not items:
            return None
        track = items[0]
        return {
            "uri": track["uri"],
            "name": track["name"],
            "artist": track["artists"][0]["name"],
        }
