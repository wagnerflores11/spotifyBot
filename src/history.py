"""Histórico local de playlists criadas pelo SpotifyBot."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import HISTORY_FILE

logger = logging.getLogger(__name__)


def _load() -> list[dict]:
    """Carrega o histórico do arquivo JSON."""
    path = Path(HISTORY_FILE)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Erro ao carregar historico: %s", exc)
        return []


def _save(entries: list[dict]) -> None:
    """Salva o histórico no arquivo JSON."""
    try:
        Path(HISTORY_FILE).write_text(
            json.dumps(entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("Erro ao salvar historico: %s", exc)


def add_entry(
    name: str,
    url: str,
    genre: str,
    track_count: int,
    reference_songs: str,
) -> None:
    """Registra uma playlist criada no histórico."""
    entries = _load()
    entries.append({
        "name": name,
        "url": url,
        "genre": genre,
        "track_count": track_count,
        "reference_songs": reference_songs,
        "created_at": datetime.now().isoformat(),
    })
    _save(entries)
    logger.debug("Historico atualizado: %s", name)


def get_entries() -> list[dict]:
    """Retorna todas as entradas do histórico."""
    return _load()


def export_playlist_to_txt(tracks: list, playlist_name: str, output_path: str) -> str:
    """Exporta uma lista de tracks para arquivo .txt."""
    lines = [f"Playlist: {playlist_name}", f"Total: {len(tracks)} musicas", ""]
    for i, track in enumerate(tracks, 1):
        lines.append(f"{i}. {track.name} - {track.artist}")

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    logger.info("Playlist exportada para %s", output_path)
    return output_path
