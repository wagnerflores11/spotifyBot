"""Modelos de dados do SpotifyBot."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Track:
    """Representa uma faixa do Spotify."""

    uri: str
    name: str
    artist: str

    def display(self) -> str:
        return f"{self.name} - {self.artist}"


@dataclass
class Playlist:
    """Representa uma playlist do Spotify."""

    id: str
    name: str
    total: int = 0
    url: str = ""

    def display(self, index: int = 0) -> str:
        prefix = f"  {index}. " if index else ""
        return f"{prefix}{self.name} ({self.total} musicas)"


@dataclass
class Recommendation:
    """Resultado da recomendação da IA."""

    genre: str
    songs: list[dict[str, str]] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.songs) == 0
