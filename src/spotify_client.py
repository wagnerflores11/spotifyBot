"""Cliente Spotify com autenticação, busca e operações de playlist."""

import logging
import threading
import time
from typing import Optional

import spotipy
from requests.adapters import HTTPAdapter
from spotipy.oauth2 import SpotifyOAuth
from urllib3.util.retry import Retry

from src.config import (
    REQUEST_MIN_INTERVAL,
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

    # Throttle global: garante intervalo mínimo entre chamadas (thread-safe)
    _throttle_lock = threading.Lock()
    _last_request_time: float = 0.0

    def __init__(self) -> None:
        try:
            self._auth_manager = SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope=SPOTIFY_SCOPES,
            )
            self._ensure_token()
            self.sp = spotipy.Spotify(auth_manager=self._auth_manager)
            self._setup_retry()
        except Exception as exc:
            raise AuthenticationError(f"Falha na autenticacao: {exc}") from exc

    def _ensure_token(self) -> None:
        """Garante que o token em cache está válido e com os scopes corretos.

        Se o token expirou, renova via refresh_token sem abrir o browser.
        Se o cache tem scopes errados (ex: subset), corrige o campo scope.
        """
        import json
        import requests as _requests

        cache_path = self._auth_manager.cache_handler.cache_path
        try:
            with open(cache_path) as f:
                cached = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return  # Sem cache — SpotifyOAuth vai pedir autenticacao normalmente

        refresh_token = cached.get("refresh_token")
        if not refresh_token:
            return

        # Verifica se o token expirou ou se o scope esta incompleto
        token_expired = time.time() >= cached.get("expires_at", 0)
        cached_scopes = set(cached.get("scope", "").split())
        required_scopes = set(SPOTIFY_SCOPES.split())
        scope_mismatch = not required_scopes.issubset(cached_scopes)

        if token_expired or scope_mismatch:
            logger.info("Renovando token Spotify (expirado=%s, scope_mismatch=%s)", token_expired, scope_mismatch)
            resp = _requests.post(
                "https://accounts.spotify.com/api/token",
                data={"grant_type": "refresh_token", "refresh_token": refresh_token},
                auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
                timeout=15,
            )
            if resp.status_code == 200:
                new = resp.json()
                cached["access_token"] = new["access_token"]
                cached["expires_in"] = new.get("expires_in", 3600)
                cached["expires_at"] = int(time.time()) + new.get("expires_in", 3600)
                cached["token_type"] = new.get("token_type", "Bearer")
                cached["scope"] = new.get("scope", " ".join(required_scopes))
                if "refresh_token" in new:
                    cached["refresh_token"] = new["refresh_token"]
                with open(cache_path, "w") as f:
                    json.dump(cached, f)
                logger.info("Token renovado com sucesso.")
            else:
                logger.warning("Falha ao renovar token: %s", resp.text)

    def _setup_retry(self) -> None:
        """Configura retry para erros de servidor (5xx), mas NAO para 429.
        O 429 é tratado manualmente para evitar sleep de horas no urllib3."""
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503],  # 429 removido — tratamos manualmente
            respect_retry_after_header=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.sp._session.mount("https://", adapter)
        self.sp._session.mount("http://", adapter)

    def _throttle(self) -> None:
        """Garante intervalo mínimo entre chamadas à API do Spotify."""
        with self._throttle_lock:
            now = time.time()
            elapsed = now - SpotifyClient._last_request_time
            if elapsed < REQUEST_MIN_INTERVAL:
                time.sleep(REQUEST_MIN_INTERVAL - elapsed)
            SpotifyClient._last_request_time = time.time()

    # --- Informações do usuário ---

    def get_username(self) -> str:
        """Retorna o display name do usuário autenticado."""
        self._throttle()
        return self.sp.current_user()["display_name"]

    def get_user_id(self) -> str:
        """Retorna o ID do usuário autenticado."""
        self._throttle()
        return self.sp.current_user()["id"]

    # --- Busca ---

    # Palavras muito comuns que nao devem ser usadas para validar match
    _STOPWORDS = {
        "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
        "um", "uma", "uns", "umas", "que", "por", "para", "com", "sem",
        "mais", "mas", "nem", "nao", "sim", "ser", "ter", "foi", "sao",
        "amor", "voce", "meu", "minha", "seu", "sua", "ele", "ela",
        "the", "and", "for", "you", "with", "from", "this", "that",
        "all", "are", "was", "not", "but", "can", "has", "had", "his",
        "her", "our", "out", "day", "one", "two", "new", "now", "way",
        "may", "how", "man", "old", "get", "let", "say", "too",
    }

    def search_direct(self, query: str) -> Optional[Track]:
        """Busca direta por texto livre — retorna o primeiro resultado sem validacao.

        Usada para musicas de referencia do usuario, onde confiamos na intencao.
        """
        return self._search(query)

    def search_track(self, name: str, artist: str) -> Optional[Track]:
        """Busca uma faixa no Spotify com 3 estrategias progressivas.

        O throttle global em _search() já garante o intervalo entre chamadas.
        """
        # Estrategia 1: busca estruturada track:/artist:
        result = self._search(f"track:{name} artist:{artist}")
        if result:
            return result

        # Estrategia 2: busca livre "artista nome"
        fallback = self._search(f"{artist} {name}")
        if fallback and self._is_valid_match(name, artist, fallback):
            logger.debug("Encontrada via fallback 1: %s", fallback.display())
            return fallback

        # Estrategia 3: busca somente pelo nome da musica
        fallback2 = self._search(name)
        if fallback2 and self._is_valid_match(name, artist, fallback2):
            logger.debug("Encontrada via fallback 2: %s", fallback2.display())
            return fallback2

        logger.debug("Nao encontrada: %s - %s", name, artist)
        return None

    def _is_valid_match(self, name: str, artist: str, track: Track) -> bool:
        """Valida se o resultado do fallback tem relacao real com a busca."""
        result_name = track.name.lower()
        result_artist = track.artist.lower()

        # Palavras significativas (>3 chars e nao sao stopwords)
        def significant_words(text: str) -> set[str]:
            return {
                w for w in text.lower().split()
                if len(w) > 3 and w not in self._STOPWORDS
            }

        name_words = significant_words(name)
        artist_words = significant_words(artist)

        # O artista DEVE bater (pelo menos uma palavra significativa)
        artist_match = any(w in result_artist for w in artist_words) if artist_words else False

        # Ou o nome da musica deve bater BEM (pelo menos uma palavra significativa)
        name_match = any(w in result_name for w in name_words) if name_words else False

        # Aceita se: artista bate OU (nome bate E artista tem alguma relacao)
        if artist_match:
            return True
        if name_match:
            # Checa se o artista tem pelo menos alguma sobreposicao parcial
            artist_partial = any(
                w in result_artist or w in result_name
                for w in artist.lower().split()
                if len(w) > 2
            )
            return artist_partial
        return False

    def _search(self, query: str) -> Optional[Track]:
        """Executa uma busca no Spotify respeitando o throttle global."""
        self._throttle()
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
        self._throttle()
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
        self._throttle()
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
        self._throttle()
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
            self._throttle()
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
            self._throttle()
            results = self.sp.current_user_saved_tracks(limit=SPOTIFY_BATCH_DELETE)
            tracks = results.get("items", [])
            if not tracks:
                break

            self._throttle()
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
