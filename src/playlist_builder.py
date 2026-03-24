"""Orquestração: IA → busca no Spotify → cria playlist."""

import logging
from typing import Optional

from src.async_search import search_tracks_parallel
from src.config import MIN_TRACKS_FOR_PLAYLIST
from src.cover_generator import generate_cover
from src.models import Playlist
from src.recommender import recommend_songs
from src.spotify_client import SpotifyClient

logger = logging.getLogger(__name__)


def build_playlist(
    spotify: SpotifyClient,
    user_input: str,
    destination: str = "new",
    target_playlist: Optional[Playlist] = None,
) -> Optional[str]:
    """Fluxo completo: IA recomenda → busca paralela no Spotify → cria/atualiza playlist."""
    print("\nConsultando IA para montar a playlist...")
    recommendation = recommend_songs(user_input)

    if recommendation.is_empty:
        print("Erro: IA nao retornou recomendacoes.")
        return None

    print(f"Genero identificado: {recommendation.genre}")
    print(f"IA sugeriu {len(recommendation.songs)} musicas. Buscando no Spotify...\n")

    # Busca paralela com asyncio (5x mais rápido que sequencial)
    found_tracks = search_tracks_parallel(spotify, recommendation.songs)

    if not found_tracks:
        print("\nNenhuma musica encontrada no Spotify.")
        return None

    if len(found_tracks) < MIN_TRACKS_FOR_PLAYLIST:
        print(f"\nApenas {len(found_tracks)} musica(s) encontrada(s). Minimo: {MIN_TRACKS_FOR_PLAYLIST}.")
        print("Provavelmente o Spotify esta com rate limit. Tente novamente em alguns minutos.")
        return None

    print(f"\n{len(found_tracks)} musicas encontradas!")
    track_uris = [t.uri for t in found_tracks]

    # Adicionar a playlist existente
    if destination == "existing" and target_playlist:
        print(f"Adicionando {len(found_tracks)} musicas em '{target_playlist.name}'...")
        spotify.add_to_playlist(target_playlist.id, track_uris)
        print(f"\nPronto! Musicas adicionadas. {target_playlist.url}")
        return target_playlist.url

    # Criar nova playlist
    title = f"DJ Waguinho - {recommendation.genre}" if recommendation.genre else "DJ Waguinho"
    print("Gerando capa da playlist...")
    cover = generate_cover(recommendation.genre, title)

    print(f"Criando playlist '{title}' com {len(found_tracks)} musicas...")
    url = spotify.create_playlist(title, track_uris, cover_base64=cover)
    print(f"\nPlaylist criada! {url}")
    return url
