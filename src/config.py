import os
from dotenv import load_dotenv

load_dotenv()

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

MAX_PLAYLIST_SIZE = 50
SPOTIFY_BATCH_DELETE = 20
SPOTIFY_BATCH_ADD = 100
