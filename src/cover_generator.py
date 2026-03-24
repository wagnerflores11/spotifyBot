import base64
import io
import requests
from PIL import Image
from openai import OpenAI
from src.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

SPOTIFY_MAX_IMAGE_SIZE = 256 * 1024


def generate_cover(genre, title):
    prompt = (
        f"Album cover art for a {genre} playlist called '{title}'. "
        "Modern, vibrant aesthetic. No text, no letters, no words. "
        "Abstract artistic style with bold colors. Square format."
    )

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        image_data = requests.get(image_url, timeout=30).content

        img = Image.open(io.BytesIO(image_data))
        img = img.convert("RGB")
        img = img.resize((300, 300), Image.LANCZOS)

        quality = 85
        while quality >= 30:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality)
            jpeg_data = buffer.getvalue()
            if len(jpeg_data) <= SPOTIFY_MAX_IMAGE_SIZE:
                return base64.b64encode(jpeg_data).decode("utf-8")
            quality -= 10

        return None
    except Exception as e:
        print(f"  Aviso: nao foi possivel gerar a capa ({e})")
        return None
