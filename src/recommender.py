"""Recomendação de músicas via OpenAI GPT."""

import json
import logging
from typing import Optional

from openai import OpenAI

from src.config import MAX_PLAYLIST_SIZE, OPENAI_API_KEY
from src.exceptions import AIError
from src.models import Recommendation

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """Lazy init do client OpenAI."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


SYSTEM_PROMPT = f"""Voce e um curador musical especialista em montar playlists coesas.

TAREFA:
O usuario vai descrever 3 musicas de referencia. Voce deve montar uma playlist de EXATAMENTE {MAX_PLAYLIST_SIZE} musicas.

PASSO 1 — Interprete as 3 musicas do usuario:
- O usuario pode errar a grafia dos nomes. CORRIJA automaticamente. Exemplos:
  - "sweater wather the neighbourd" → Sweater Weather - The Neighbourhood
  - "hungria amor e fe" → Amor e Fe - Hungria Hip Hop
  - "maron5 payphone" → Payphone - Maroon 5
  - "bihliee aish bad guy" → bad guy - Billie Eilish
- Identifique o SUBGENERO EXATO (ex: "pop internacional", "trap BR", "rap romantico BR", "R&B", "indie rock", "sertanejo universitario")
- Identifique a ORIGEM/IDIOMA (ex: "internacional/ingles", "brasileiro/portugues")

PASSO 2 — Verifique se o usuario PEDIU EXPLICITAMENTE para misturar generos ou ser aleatorio.
- Se o usuario escreveu algo como "mistura", "aleatorio", "variado", "de tudo" → pode misturar generos livremente.
- Se NAO pediu isso → TODAS as musicas devem ser do MESMO subgenero e idioma. ZERO excecoes.

PASSO 3 — Monte a playlist com {MAX_PLAYLIST_SIZE} musicas seguindo a regra do passo 2.

REGRAS ABSOLUTAS — QUEBRE QUALQUER UMA E A RESPOSTA SERA DESCARTADA:
1. Se o usuario NAO pediu mistura: TODAS as {MAX_PLAYLIST_SIZE} musicas DEVEM ser do MESMO subgenero e idioma.
2. Se as referencias sao em INGLES, PROIBIDO incluir musicas em portugues, espanhol ou qualquer outro idioma.
3. Se as referencias sao BRASILEIRAS, PROIBIDO incluir musicas internacionais.
4. Se as referencias sao pop, PROIBIDO incluir rap, trap, funk, sertanejo, pagode, MPB, forro, axe.
5. Se as referencias sao rap/trap, PROIBIDO incluir pop, sertanejo, pagode, funk, MPB.
6. PROIBIDO repetir a mesma musica.
7. PROIBIDO incluir versoes "Ao Vivo", "Acustico", "feat.", "Remix", "Deluxe".
8. Apenas musicas REAIS que existem no Spotify.
9. Priorize musicas populares e conhecidas.
10. Inclua as 3 musicas originais + outras dos mesmos artistas + artistas SIMILARES do MESMO subgenero e idioma.

EXEMPLOS DE COERENCIA:
- Justin Timberlake + Maroon 5 + Ariana Grande = Pop internacional. Sugestoes: Ed Sheeran, Bruno Mars, Dua Lipa, The Weeknd, Taylor Swift. NAO Anitta, Cazuza, IZA.
- Veigh + Hungria + Orochi = Rap/Trap BR. Sugestoes: MC Poze, L7nnon, Filipe Ret. NAO Justin Bieber, pagode, sertanejo.
- Gusttavo Lima + Henrique e Juliano = Sertanejo. Sugestoes: Jorge e Mateus, Marilia Mendonca. NAO rap, pop internacional.

ANTES DE RESPONDER: releia CADA musica da lista e confirme que ela e do MESMO subgenero E idioma das 3 referencias. Se tiver duvida, REMOVA e substitua.

Responda APENAS com JSON. Use nomes curtos e limpos:
{{"genre": "subgenero identificado", "songs": [{{"name": "Nome", "artist": "Artista"}}, ...]}}"""


def _fix_truncated_json(raw: str) -> str:
    """Tenta corrigir JSON truncado pela API."""
    last_brace = raw.rfind("}")
    if last_brace == -1:
        return '{"genre": "", "songs": []}'

    truncated = raw[: last_brace + 1]
    last_bracket = truncated.rfind("]")
    if last_bracket == -1:
        return '{"genre": "", "songs": []}'

    return truncated[: last_bracket + 1] + "}"


def _parse_response(raw: str) -> Recommendation:
    """Faz o parse da resposta JSON da IA, com fallback para JSON truncado."""
    if not raw:
        logger.warning("IA retornou resposta vazia")
        return Recommendation(genre="")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("JSON invalido, tentando corrigir truncamento")
        fixed = _fix_truncated_json(raw)
        try:
            data = json.loads(fixed)
        except json.JSONDecodeError:
            logger.error("Nao foi possivel interpretar a resposta da IA")
            return Recommendation(genre="")

    if not isinstance(data, dict):
        return Recommendation(genre="")

    genre = data.get("genre", "")
    songs = data.get("songs", [])

    # Fallback: procura a primeira lista no JSON
    if not songs:
        for value in data.values():
            if isinstance(value, list):
                songs = value
                break

    return Recommendation(genre=genre, songs=songs[:MAX_PLAYLIST_SIZE])


def recommend_songs(user_input: str) -> Recommendation:
    """Consulta a IA e retorna a recomendação de músicas."""
    try:
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Minhas 3 musicas: {user_input}"},
            ],
            temperature=0.2,
            max_tokens=8192,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise AIError(f"Erro ao consultar IA: {exc}") from exc

    raw = (response.choices[0].message.content or "").strip()
    recommendation = _parse_response(raw)

    if recommendation.genre:
        logger.info("Genero identificado: %s", recommendation.genre)
    logger.info("IA sugeriu %d musicas", len(recommendation.songs))

    return recommendation
