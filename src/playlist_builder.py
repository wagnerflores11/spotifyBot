"""Orquestração: IA → busca no Spotify → cria playlist."""

import logging
from typing import Optional

from src.async_search import search_tracks_parallel
from src.config import MIN_TRACKS_FOR_PLAYLIST
from src.cover_generator import generate_cover
from src.models import Playlist, Track
from src.recommender import recommend_songs
from src.spotify_client import SpotifyClient

logger = logging.getLogger(__name__)


def _search_reference_songs(spotify: SpotifyClient, user_input: str) -> list[Track]:
    """Busca as musicas de referencia do usuario diretamente no Spotify.

    Tenta multiplas estrategias:
    1. Busca direta com o texto completo
    2. Se tem formato "artista musica", tenta busca estruturada
    3. Tenta invertendo a ordem das palavras
    """
    raw_songs = [s.strip() for s in user_input.split(",") if s.strip()]
    ref_tracks: list[Track] = []
    seen_uris: set[str] = set()

    print(f"\nBuscando {len(raw_songs)} musica(s) de referencia no Spotify...")
    for i, song in enumerate(raw_songs, 1):
        result = None

        # Se tem " - ", usa como separador artista/musica
        if " - " in song:
            parts = song.split(" - ", 1)
            result = spotify.search_direct(f"track:{parts[1].strip()} artist:{parts[0].strip()}")

        if not result:
            # Tenta busca direta com texto completo
            result = spotify.search_direct(song)

        if result and result.uri not in seen_uris:
            print(f"  [{i}/{len(raw_songs)}] [OK] {result.display()}")
            ref_tracks.append(result)
            seen_uris.add(result.uri)
        else:
            print(f"  [{i}/{len(raw_songs)}] [--] {song} (nao encontrada)")

    return ref_tracks


def build_playlist(
    spotify: SpotifyClient,
    user_input: str,
    destination: str = "new",
    target_playlist: Optional[Playlist] = None,
) -> Optional[str]:
    """Fluxo completo: busca referencias → IA recomenda → busca paralela → cria playlist."""

    # 1. Busca as musicas de referencia do usuario PRIMEIRO
    ref_tracks = _search_reference_songs(spotify, user_input)
    ref_uris = {t.uri for t in ref_tracks}

    if ref_tracks:
        print(f"\n{len(ref_tracks)} musica(s) de referencia encontrada(s).")
    else:
        print("\nNenhuma musica de referencia encontrada no Spotify.")

    # 2. Consulta a IA para completar a playlist
    print("\nConsultando IA para montar a playlist...")
    recommendation = recommend_songs(user_input)

    if recommendation.is_empty:
        print("Erro: IA nao retornou recomendacoes.")
        return None

    print(f"Genero identificado: {recommendation.genre}")
    print(f"IA sugeriu {len(recommendation.songs)} musicas. Buscando no Spotify...\n")

    # 3. Busca paralela das sugestoes da IA
    ai_tracks = search_tracks_parallel(spotify, recommendation.songs)

    # 4. Monta a lista final: referencias primeiro, depois IA (sem duplicar)
    final_tracks: list[Track] = list(ref_tracks)
    seen_uris = set(ref_uris)

    for track in ai_tracks:
        if track.uri not in seen_uris:
            final_tracks.append(track)
            seen_uris.add(track.uri)

    if not final_tracks:
        print("\nNenhuma musica encontrada no Spotify.")
        return None

    if len(final_tracks) < MIN_TRACKS_FOR_PLAYLIST:
        print(f"\nApenas {len(final_tracks)} musica(s) encontrada(s). Minimo: {MIN_TRACKS_FOR_PLAYLIST}.")
        print("Provavelmente o Spotify esta com rate limit. Tente novamente em alguns minutos.")
        return None

    print(f"\n{len(final_tracks)} musicas na playlist ({len(ref_tracks)} de referencia + {len(final_tracks) - len(ref_tracks)} da IA)!")
    track_uris = [t.uri for t in final_tracks]

    # Adicionar a playlist existente
    if destination == "existing" and target_playlist:
        print(f"Adicionando {len(final_tracks)} musicas em '{target_playlist.name}'...")
        spotify.add_to_playlist(target_playlist.id, track_uris)
        print(f"\nPronto! Musicas adicionadas. {target_playlist.url}")
        return target_playlist.url

    # Criar nova playlist
    title = f"DJ Waguinho - {recommendation.genre}" if recommendation.genre else "DJ Waguinho"
    print("Gerando capa da playlist...")
    cover = generate_cover(recommendation.genre, title)

    print(f"Criando playlist '{title}' com {len(final_tracks)} musicas...")
    url = spotify.create_playlist(title, track_uris, cover_base64=cover)
    print(f"\nPlaylist criada! {url}")
    return url
