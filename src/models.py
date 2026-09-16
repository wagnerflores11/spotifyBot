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
    total: Optional[int] = None  # None quando a API não informa a contagem
    url: str = ""

    @property
    def count_label(self) -> str:
        """Sufixo '(N musicas)' apenas quando a contagem é conhecida."""
        return f" ({self.total} musicas)" if self.total is not None else ""

    def display(self, index: int = 0) -> str:
        prefix = f"  {index}. " if index else ""
        return f"{prefix}{self.name}{self.count_label}"


@dataclass
class Recommendation:
    """Resultado da recomendação da IA."""

    genre: str
    songs: list[dict[str, str]] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.songs) == 0


@dataclass
class BuildResult:
    """Resultado da montagem de uma playlist — usado para registrar o histórico."""

    url: str
    title: str
    genre: str
    track_count: int
