import base64
import requests
from openai import OpenAI
from src.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_cover(genre, title):
    prompt = (
        f"Album cover art for a Brazilian {genre} playlist called '{title}'. "
        "Modern, vibrant, urban aesthetic. No text, no letters, no words. "
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
        return base64.b64encode(image_data).decode("utf-8")
    except Exception as e:
        print(f"  Aviso: nao foi possivel gerar a capa ({e})")
        return None
