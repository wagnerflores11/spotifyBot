"""Configurações e validação de variáveis de ambiente."""

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# --- Spotify ---
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SPOTIFY_SCOPES = (
    "user-library-read "
    "user-library-modify "
    "playlist-modify-public "
    "playlist-modify-private "
    "playlist-read-private "
    "ugc-image-upload"
)

# --- Limites ---
MAX_PLAYLIST_SIZE = 50
SPOTIFY_BATCH_DELETE = 20
SPOTIFY_BATCH_ADD = 100
RATE_LIMIT_WAIT_SECONDS = 35   # delay ao receber 429 (acima do rolling window de 30s)
MIN_TRACKS_FOR_PLAYLIST = 30
ASYNC_CONCURRENCY = 2          # buscas simultâneas — conservador para dev apps
ASYNC_BATCH_DELAY = 2.0        # delay entre buscas (1.0s por busca = 60 req/min max)
REQUEST_MIN_INTERVAL = 0.8     # intervalo mínimo entre qualquer chamada à API

# --- Caminhos ---
HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "history.json")

# --- Logging ---
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"


def setup_logging(verbose: bool = False) -> None:
    """Configura o logging da aplicação."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def validate_config() -> list[str]:
    """Retorna lista de variáveis obrigatórias que estão faltando."""
    required = {
        "SPOTIFY_CLIENT_ID": SPOTIFY_CLIENT_ID,
        "SPOTIFY_CLIENT_SECRET": SPOTIFY_CLIENT_SECRET,
        "OPENAI_API_KEY": OPENAI_API_KEY,
    }
    return [key for key, value in required.items() if not value]
