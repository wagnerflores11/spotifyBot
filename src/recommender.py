import json
from openai import OpenAI
from src.config import OPENAI_API_KEY, MAX_PLAYLIST_SIZE

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = f"""Voce e um curador musical especialista. O usuario vai descrever 3 musicas de referencia.

Sua tarefa:
1. Identifique o GENERO e ESTILO exato dessas 3 musicas (ex: trap brasileiro, rap nacional, funk melody, sertanejo universitario, pagode, etc.)
2. Monte uma playlist de exatamente {MAX_PLAYLIST_SIZE} musicas que sejam DO MESMO GENERO E ESTILO das 3 musicas informadas
3. Inclua as 3 musicas originais na playlist
4. Inclua outras musicas populares dos mesmos artistas
5. Inclua musicas de artistas semelhantes que fazem o MESMO ESTILO

REGRAS:
- NAO misture generos. Se as 3 musicas sao rap/trap, a playlist inteira deve ser rap/trap.
- NAO repita a mesma musica mais de uma vez.
- Priorize musicas conhecidas e populares.
- Responda APENAS com JSON valido no formato:
  {{"songs": [{{"name": "Nome", "artist": "Artista"}}, ...]}}"""


def recommend_songs(user_input):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Minhas 3 musicas: {user_input}"},
        ],
        temperature=0.7,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    data = json.loads(raw)

    if isinstance(data, dict):
        for key in data:
            if isinstance(data[key], list):
                return data[key][:MAX_PLAYLIST_SIZE]
    if isinstance(data, list):
        return data[:MAX_PLAYLIST_SIZE]

    return []
