"""Geração de capas de playlist via DALL-E 3."""

import base64
import io
import logging
from typing import Optional

import requests
from openai import OpenAI
from PIL import Image

from src.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

SPOTIFY_MAX_IMAGE_BYTES = 256 * 1024
COVER_SIZE = (300, 300)
QUALITY_RANGE = range(85, 25, -10)

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """Lazy init do client OpenAI."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _compress_to_base64(image_data: bytes) -> Optional[str]:
    """Redimensiona e comprime a imagem até caber no limite do Spotify."""
    img = Image.open(io.BytesIO(image_data)).convert("RGB")
    img = img.resize(COVER_SIZE, Image.LANCZOS)

    for quality in QUALITY_RANGE:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        jpeg_data = buffer.getvalue()

        if len(jpeg_data) <= SPOTIFY_MAX_IMAGE_BYTES:
            logger.debug("Capa comprimida com quality=%d (%d bytes)", quality, len(jpeg_data))
            return base64.b64encode(jpeg_data).decode("utf-8")

    logger.warning("Nao foi possivel comprimir a capa abaixo de %d bytes", SPOTIFY_MAX_IMAGE_BYTES)
    return None


def generate_cover(genre: str, title: str) -> Optional[str]:
    """Gera uma capa de playlist com DALL-E 3. Retorna base64 ou None."""
    prompt = (
        f"Album cover art for a {genre} playlist called '{title}'. "
        "Modern, vibrant aesthetic. No text, no letters, no words. "
        "Abstract artistic style with bold colors. Square format."
    )

    try:
        response = _get_client().images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        image_data = requests.get(image_url, timeout=30).content
        return _compress_to_base64(image_data)

    except Exception as exc:
        logger.warning("Nao foi possivel gerar a capa: %s", exc)
        return None
