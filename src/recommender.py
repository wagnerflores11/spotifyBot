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
O usuario vai informar musicas de referencia (podem ser 1, 3, 5 ou mais). Voce deve montar uma playlist de EXATAMENTE {MAX_PLAYLIST_SIZE} musicas baseada nessas referencias.

PASSO 1 — Interprete as musicas do usuario:
- O usuario pode errar a grafia dos nomes. CORRIJA automaticamente. Exemplos:
  - "sweater wather the neighbourd" → Sweater Weather - The Neighbourhood
  - "hungria amor e fe" → Amor e Fe - Hungria Hip Hop
  - "maron5 payphone" → Payphone - Maroon 5
  - "rubel quando bate aquela saudade" → Quando Bate Aquela Saudade - Rubel
  - "fresno milonga" → Milonga - Fresno (ou Milonga Para Uma Outra Vida, se for o caso)
- Identifique o ESTILO/VIBE GERAL que conecta as referencias (ex: "MPB contemporaneo", "rock alternativo BR", "indie brasileiro", "pop brasileiro", "trap BR")
- Identifique a ORIGEM/IDIOMA (ex: "internacional/ingles", "brasileiro/portugues")

PASSO 2 — Analise se as referencias do usuario pertencem ao MESMO genero ou a generos DIFERENTES:
- Se todas as referencias sao do mesmo genero (ex: todas rap BR) → mantenha TODAS as musicas nesse genero.
- Se as referencias MISTURAM generos (ex: MPB + rock + indie) → identifique a VIBE/SENTIMENTO que conecta essas musicas (ex: "musica brasileira autoral/alternativa", "musica introspectiva brasileira") e monte a playlist seguindo essa vibe. Pode incluir artistas de subgeneros diferentes DESDE QUE compartilhem a mesma energia e idioma.

PASSO 3 — Monte a playlist com {MAX_PLAYLIST_SIZE} musicas.

REGRAS ABSOLUTAS:
1. Se as referencias sao em INGLES, PROIBIDO incluir musicas em portugues, espanhol ou qualquer outro idioma.
2. Se as referencias sao BRASILEIRAS, PROIBIDO incluir musicas internacionais.
3. PROIBIDO repetir a mesma musica. Cada entrada deve ser UNICA — nome e artista diferentes.
4. PROIBIDO incluir versoes "Ao Vivo", "Acustico", "Remix", "Deluxe", "Live".
5. Apenas musicas REAIS que existem no Spotify. Use o nome EXATO como aparece no Spotify.
6. Priorize musicas populares e conhecidas (com muitos streams).
7. Inclua as musicas originais do usuario + outras dos mesmos artistas + artistas SIMILARES.
8. Se as referencias misturam generos, a playlist pode misturar tambem, mas MANTENHA o mesmo idioma e a mesma vibe/energia.
9. Versoes "feat." sao permitidas SOMENTE se forem a versao principal da musica no Spotify.
10. DIVERSIDADE DE ARTISTAS: maximo 3 musicas por artista. Inclua pelo menos 15 artistas DIFERENTES na playlist. Priorize variedade.

EXEMPLOS DE COERENCIA:
- Justin Timberlake + Maroon 5 + Ariana Grande = Pop internacional. Sugestoes: Ed Sheeran, Bruno Mars, Dua Lipa. NAO Anitta, IZA.
- Veigh + Hungria + Orochi = Rap/Trap BR. Sugestoes: MC Poze, L7nnon, Filipe Ret. NAO Justin Bieber, pagode.
- Rubel + Anavitoria + Fresno = Musica brasileira autoral/alternativa. Sugestoes: Los Hermanos, Nando Reis, Tiago Iorc, Silva, Scalene, Lagum, Melim. NAO rap, funk, sertanejo, pagode.
- Gusttavo Lima + Henrique e Juliano = Sertanejo. Sugestoes: Jorge e Mateus, Marilia Mendonca. NAO rap, pop internacional.

ANTES DE RESPONDER:
1. Releia CADA musica da lista e confirme que ela combina com a vibe E o idioma das referencias. Se tiver duvida, REMOVA e substitua.
2. Verifique que NENHUMA musica se repete na lista. Se repetir, substitua por outra.
3. Verifique que nenhum artista aparece mais de 3 vezes. Se aparecer, substitua as extras por musicas de artistas diferentes.
4. Confirme que voce tem EXATAMENTE {MAX_PLAYLIST_SIZE} musicas UNICAS na lista.

Responda APENAS com JSON. Use nomes curtos e limpos:
{{"genre": "estilo/vibe identificado", "songs": [{{"name": "Nome", "artist": "Artista"}}, ...]}}"""


def _song_key(song: dict) -> str:
    """Gera chave de deduplicacao normalizada para uma musica."""
    return f"{song.get('name', '').lower().strip()}|{song.get('artist', '').lower().strip()}"


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

    # Deduplica musicas antes de retornar (IA pode repetir)
    seen: set[str] = set()
    unique_songs: list[dict] = []
    for song in songs:
        key = _song_key(song)
        if key not in seen:
            seen.add(key)
            unique_songs.append(song)

    if len(unique_songs) < len(songs):
        logger.info("Removidas %d duplicatas da IA", len(songs) - len(unique_songs))

    return Recommendation(genre=genre, songs=unique_songs[:MAX_PLAYLIST_SIZE])


def _call_ai(messages: list[dict[str, str]], temperature: float = 0.3) -> str:
    """Faz uma chamada à API da OpenAI e retorna o conteúdo."""
    try:
        response = _get_client().chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=temperature,
            max_tokens=8192,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise AIError(f"Erro ao consultar IA: {exc}") from exc
    return (response.choices[0].message.content or "").strip()


def recommend_songs(user_input: str) -> Recommendation:
    """Consulta a IA e retorna a recomendação de músicas, com suplementação se necessário."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Minhas musicas de referencia: {user_input}"},
    ]

    raw = _call_ai(messages, temperature=0.3)
    recommendation = _parse_response(raw)

    if recommendation.genre:
        logger.info("Genero identificado: %s", recommendation.genre)
    logger.info("IA sugeriu %d musicas", len(recommendation.songs))

    # Se a IA retornou poucas musicas, pede mais em uma segunda chamada
    if len(recommendation.songs) < MAX_PLAYLIST_SIZE:
        existing_names = [
            f"{s.get('name', '')} - {s.get('artist', '')}"
            for s in recommendation.songs
        ]
        existing_list = "\n".join(existing_names)
        supplement_msg = (
            f"Voce ja sugeriu {len(recommendation.songs)} musicas, "
            f"mas preciso de {MAX_PLAYLIST_SIZE}. "
            f"Sugira mais {MAX_PLAYLIST_SIZE - len(recommendation.songs)} musicas "
            f"do MESMO estilo ({recommendation.genre}) que NAO estejam nesta lista:\n"
            f"{existing_list}\n\n"
            f"Responda APENAS com JSON no mesmo formato: "
            f'{{"genre": "{recommendation.genre}", "songs": [...]}}'
        )
        messages.append({"role": "assistant", "content": raw})
        messages.append({"role": "user", "content": supplement_msg})

        logger.info("Pedindo mais musicas (faltam %d)", MAX_PLAYLIST_SIZE - len(recommendation.songs))
        raw2 = _call_ai(messages, temperature=0.5)
        supplement = _parse_response(raw2)

        if supplement.songs:
            # Deduplica contra as ja existentes usando _song_key
            existing_keys = {_song_key(s) for s in recommendation.songs}
            for song in supplement.songs:
                key = _song_key(song)
                if key not in existing_keys:
                    recommendation.songs.append(song)
                    existing_keys.add(key)

            logger.info("Total apos suplemento: %d musicas", len(recommendation.songs))

    return recommendation
