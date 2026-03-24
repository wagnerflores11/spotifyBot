"""Cliente Spotify com autenticação, busca e operações de playlist."""

import logging
import time
from typing import Optional

import spotipy
from requests.adapters import HTTPAdapter
from spotipy.oauth2 import SpotifyOAuth
from urllib3.util.retry import Retry

from src.config import (
    SPOTIFY_BATCH_ADD,
    SPOTIFY_BATCH_DELETE,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_SCOPES,
)
from src.exceptions import AuthenticationError, RateLimitError
from src.models import Playlist, Track

logger = logging.getLogger(__name__)


class SpotifyClient:
    """Encapsula toda a comunicação com a API do Spotify."""

    def __init__(self) -> None:
        try:
            auth_manager = SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope=SPOTIFY_SCOPES,
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            self._setup_retry()
        except Exception as exc:
            raise AuthenticationError(f"Falha na autenticacao: {exc}") from exc

    def _setup_retry(self) -> None:
        """Configura retry automático para erros transientes."""
        retry = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503],
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.sp._session.mount("https://", adapter)
        self.sp._session.mount("http://", adapter)

    # --- Informações do usuário ---

    def get_username(self) -> str:
        """Retorna o display name do usuário autenticado."""
        return self.sp.current_user()["display_name"]

    def get_user_id(self) -> str:
        """Retorna o ID do usuário autenticado."""
        return self.sp.current_user()["id"]

    # --- Busca ---

    def search_track(self, name: str, artist: str) -> Optional[Track]:
        """Busca uma faixa no Spotify. Tenta busca exata, depois busca livre."""
        query = f"track:{name} artist:{artist}"
        result = self._search(query)
        if result:
            return result

        time.sleep(0.5)
        fallback = self._search(f"{name} {artist}")
        if fallback:
            logger.debug("Encontrada via fallback: %s", fallback.display())
        return fallback

    def _search(self, query: str) -> Optional[Track]:
        """Executa uma busca no Spotify e retorna o primeiro resultado."""
        try:
            results = self.sp.search(q=query, type="track", limit=1)
        except spotipy.exceptions.SpotifyException as exc:
            if exc.http_status == 429:
                raise RateLimitError()
            raise

        items = results.get("tracks", {}).get("items", [])
        if not items:
            return None

        track = items[0]
        return Track(
            uri=track["uri"],
            name=track["name"],
            artist=track["artists"][0]["name"],
        )

    # --- Playlists ---

    def get_my_playlists(self) -> list[Playlist]:
        """Retorna todas as playlists do usuário com paginação."""
        playlists: list[Playlist] = []
        results = self.sp.current_user_playlists(limit=50)

        while results:
            for item in results["items"]:
                playlists.append(Playlist(
                    id=item["id"],
                    name=item["name"],
                    total=item.get("tracks", {}).get("total", 0),
                    url=item.get("external_urls", {}).get("spotify", ""),
                ))
            if results.get("next"):
                results = self.sp.next(results)
            else:
                break

        return playlists

    def get_playlist_tracks(self, playlist_id: str) -> list[Track]:
        """Retorna todas as faixas de uma playlist."""
        tracks: list[Track] = []
        results = self.sp.playlist_tracks(playlist_id, limit=100)

        while results:
            for item in results["items"]:
                t = item.get("track")
                if t and t.get("uri"):
                    tracks.append(Track(
                        uri=t["uri"],
                        name=t.get("name", "Desconhecida"),
                        artist=t["artists"][0]["name"] if t.get("artists") else "Desconhecido",
                    ))
            if results.get("next"):
                results = self.sp.next(results)
            else:
                break

        return tracks

    def create_playlist(
        self,
        name: str,
        track_uris: list[str],
        cover_base64: Optional[str] = None,
        description: str = "Criada pelo SpotifyBot",
    ) -> str:
        """Cria uma playlist e retorna a URL."""
        payload = {"name": name, "public": False, "description": description}
        response = self.sp._post("me/playlists", payload=payload)
        playlist_id = response["id"]

        if cover_base64:
            self._upload_cover(playlist_id, cover_base64)

        self.add_to_playlist(playlist_id, track_uris)
        logger.info("Playlist '%s' criada com %d faixas", name, len(track_uris))
        return response["external_urls"]["spotify"]

    def add_to_playlist(self, playlist_id: str, track_uris: list[str]) -> None:
        """Adiciona faixas a uma playlist existente (em lotes)."""
        for i in range(0, len(track_uris), SPOTIFY_BATCH_ADD):
            batch = track_uris[i : i + SPOTIFY_BATCH_ADD]
            self.sp.playlist_add_items(playlist_id, batch)
        logger.info("Adicionadas %d faixas à playlist %s", len(track_uris), playlist_id)

    def duplicate_playlist(self, source: Playlist, new_name: Optional[str] = None) -> str:
        """Duplica uma playlist inteira e retorna a URL da nova."""
        tracks = self.get_playlist_tracks(source.id)
        if not tracks:
            logger.warning("Playlist '%s' esta vazia, nada para duplicar", source.name)
            return ""

        name = new_name or f"{source.name} (copia)"
        uris = [t.uri for t in tracks]
        return self.create_playlist(name, uris, description=f"Copia de '{source.name}'")

    def delete_playlist(self, playlist_id: str) -> None:
        """Remove (unfollow) uma playlist."""
        self.sp.current_user_unfollow_playlist(playlist_id)
        logger.info("Playlist %s removida", playlist_id)

    # --- Curtidas ---

    def remove_all_liked_songs(self) -> int:
        """Remove todas as músicas curtidas e retorna o total removido."""
        total_removed = 0
        while True:
            results = self.sp.current_user_saved_tracks(limit=SPOTIFY_BATCH_DELETE)
            tracks = results.get("items", [])
            if not tracks:
                break

            track_ids = [t["track"]["id"] for t in tracks]
            self.sp.current_user_saved_tracks_delete(tracks=track_ids)
            total_removed += len(track_ids)
            logger.info("Removidas %d curtidas (total: %d)", len(track_ids), total_removed)

        return total_removed

    # --- Helpers ---

    def _upload_cover(self, playlist_id: str, cover_base64: str) -> None:
        """Tenta fazer upload da capa da playlist."""
        try:
            self.sp.playlist_upload_cover_image(playlist_id, cover_base64)
        except Exception as exc:
            logger.warning("Nao foi possivel definir a capa: %s", exc)
