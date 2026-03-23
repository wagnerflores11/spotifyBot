import json
from openai import OpenAI
from src.config import OPENAI_API_KEY, MAX_PLAYLIST_SIZE

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = f"""Voce e um curador musical brasileiro especialista em montar playlists coesas.

TAREFA:
O usuario vai descrever 3 musicas de referencia. Voce deve montar uma playlist de EXATAMENTE {MAX_PLAYLIST_SIZE} musicas.

PASSO 1 — Identifique o SUBGENERO EXATO das 3 musicas.
Nao use generos amplos como "brasileiro" ou "nacional".
Exemplos de subgeneros validos:
- Rap romantico BR (Hungria, Orochi, Mc Pedrinho)
- Trap BR (Veigh, Matuê, Yunk Vino)
- Rap consciente BR (Emicida, Djonga, Racionais)
- Funk melody (Mc Kevinho, Livinho)
- Funk ostentacao (Mc IG, Mc Ryan SP)
- Sertanejo universitario (Gusttavo Lima, Henrique e Juliano)
- Pagode (Menos e Mais, Thiaguinho)
- Pop BR (Anitta, Ludmilla)

PASSO 2 — Monte a playlist com {MAX_PLAYLIST_SIZE} musicas que sejam TODAS do subgenero identificado.

PASSO 3 — Crie um titulo criativo para a playlist que combine com o estilo musical. Exemplos:
- Para rap romantico: "Noites de Rap & Sentimento"
- Para trap: "Trap Session BR"
- Para funk: "Baile do Momento"
NAO use "SpotifyBot" no titulo.

REGRAS ABSOLUTAS — QUEBRE QUALQUER UMA E A RESPOSTA SERA DESCARTADA:
1. TODAS as {MAX_PLAYLIST_SIZE} musicas DEVEM ser do MESMO subgenero. ZERO excecoes.
2. Se as referencias sao rap/trap, PROIBIDO incluir: pagode, sertanejo, MPB, pop, funk, forro, axe, reggae.
3. Se as referencias sao sertanejo, PROIBIDO incluir: rap, trap, funk, pagode, MPB, pop.
4. PROIBIDO repetir a mesma musica.
5. PROIBIDO incluir versoes "Ao Vivo", "Acustico", "feat.", "Remix".
6. Apenas musicas REAIS que existem no Spotify.
7. Priorize musicas populares e conhecidas dos artistas.
8. Inclua as 3 musicas originais + outras dos mesmos artistas + artistas SIMILARES do MESMO subgenero.

ANTES DE RESPONDER: releia cada musica da lista e confirme mentalmente que ela pertence ao subgenero identificado. Se tiver duvida sobre alguma, REMOVA e substitua.

Responda APENAS com JSON. Use nomes curtos e limpos:
{{"title": "Titulo Criativo", "genre": "subgenero", "songs": [{{"name": "Nome", "artist": "Artista"}}, ...]}}"""


def _fix_truncated_json(raw):
    last_brace = raw.rfind("}")
    if last_brace == -1:
        return '{"songs": []}'
    truncated = raw[:last_brace + 1]
    last_bracket = truncated.rfind("]")
    if last_bracket == -1:
        return '{"songs": []}'
    return truncated[:last_bracket + 1] + "}"


def recommend_songs(user_input):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Minhas 3 musicas: {user_input}"},
        ],
        temperature=0.2,
        max_tokens=8192,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raw = _fix_truncated_json(raw)
        data = json.loads(raw)

    if not isinstance(data, dict):
        return "", "", []

    genre = data.get("genre", "")
    title = data.get("title", "")
    songs = data.get("songs", [])

    if genre:
        print(f"Genero identificado: {genre}")
    if title:
        print(f"Titulo da playlist: {title}")

    if not songs:
        for key in data:
            if isinstance(data[key], list):
                songs = data[key]
                break

    return title, genre, songs[:MAX_PLAYLIST_SIZE]
