import spotipy
from spotipy.oauth2 import SpotifyOAuth
from src.config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_SCOPES,
    SPOTIFY_BATCH_DELETE,
    SPOTIFY_BATCH_ADD,
)


class SpotifyClient:

    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=SPOTIFY_SCOPES,
        ))

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
        if result:
            return result
        return self._search(f"{name} {artist}")

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
        results = self.sp.search(q=query, type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])
        if not items:
            return None
        track = items[0]
        return {
            "uri": track["uri"],
            "name": track["name"],
            "artist": track["artists"][0]["name"],
        }
