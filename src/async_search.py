"""Busca paralela de faixas no Spotify usando asyncio.

Em vez de buscar uma música por vez (sequencial ~75s para 50 músicas),
dispara várias buscas simultâneas em lotes controlados por um semáforo.
Com 5 buscas paralelas, o tempo cai para ~15s.

Como o spotipy é síncrono, usamos asyncio.to_thread() para rodar cada
chamada HTTP numa thread separada sem bloquear o event loop.
"""

import asyncio
import logging
import time
from typing import Optional

from src.config import ASYNC_BATCH_DELAY, ASYNC_CONCURRENCY, RATE_LIMIT_WAIT_SECONDS
from src.exceptions import RateLimitError
from src.models import Track
from src.spotify_client import SpotifyClient

logger = logging.getLogger(__name__)


async def _search_one(
    spotify: SpotifyClient,
    name: str,
    artist: str,
    index: int,
    total: int,
    semaphore: asyncio.Semaphore,
) -> Optional[Track]:
    """Busca uma faixa respeitando o semáforo de concorrência."""
    async with semaphore:
        try:
            # to_thread roda a função síncrona do spotipy numa thread
            result = await asyncio.to_thread(spotify.search_track, name, artist)
        except RateLimitError:
            logger.warning("Rate limit na busca #%d. Aguardando %ds...", index, RATE_LIMIT_WAIT_SECONDS)
            await asyncio.sleep(RATE_LIMIT_WAIT_SECONDS)
            try:
                result = await asyncio.to_thread(spotify.search_track, name, artist)
            except RateLimitError:
                logger.error("Rate limit persistente na busca #%d. Pulando.", index)
                print(f"  [{index}/{total}] [!!] {name} - {artist} (rate limit)")
                return None

        if result:
            print(f"  [{index}/{total}] [OK] {result.display()}")
        else:
            print(f"  [{index}/{total}] [--] {name} - {artist}")

        # Pequeno delay entre buscas individuais para não estourar rate limit
        await asyncio.sleep(ASYNC_BATCH_DELAY / ASYNC_CONCURRENCY)
        return result


async def _search_all(
    spotify: SpotifyClient,
    recommendations: list[dict],
) -> list[Track]:
    """Dispara buscas em paralelo com semáforo de concorrência."""
    semaphore = asyncio.Semaphore(ASYNC_CONCURRENCY)
    total = len(recommendations)

    tasks = [
        _search_one(
            spotify=spotify,
            name=rec.get("name", ""),
            artist=rec.get("artist", ""),
            index=i,
            total=total,
            semaphore=semaphore,
        )
        for i, rec in enumerate(recommendations, 1)
    ]

    results = await asyncio.gather(*tasks)

    # Deduplicar e filtrar None
    seen_uris: set[str] = set()
    tracks: list[Track] = []
    for track in results:
        if track and track.uri not in seen_uris:
            seen_uris.add(track.uri)
            tracks.append(track)

    return tracks


def search_tracks_parallel(
    spotify: SpotifyClient,
    recommendations: list[dict],
) -> list[Track]:
    """Entry point síncrono — roda a busca paralela via asyncio.

    Pode ser chamado de código síncrono normalmente:
        tracks = search_tracks_parallel(spotify, recs)
    """
    start = time.time()
    logger.info(
        "Iniciando busca paralela: %d musicas, concorrencia=%d",
        len(recommendations),
        ASYNC_CONCURRENCY,
    )

    tracks = asyncio.run(_search_all(spotify, recommendations))

    elapsed = time.time() - start
    logger.info("Busca concluida: %d encontradas em %.1fs", len(tracks), elapsed)
    print(f"\n  Busca concluida em {elapsed:.1f}s ({len(tracks)} encontradas)")

    return tracks
