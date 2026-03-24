import time

from src.spotify_client import SpotifyClient
from src.recommender import recommend_songs
from src.cover_generator import generate_cover

SEARCH_DELAY = 1.5
MIN_TRACKS = 5


def _search_tracks(spotify, recommendations):
    found_tracks = []
    seen_uris = set()

    for i, rec in enumerate(recommendations, 1):
        result = spotify.search_track(rec["name"], rec["artist"])
        if result == "RATE_LIMITED":
            print("\n  Spotify bloqueou as requisicoes. Aguardando 30s...")
            time.sleep(30)
            result = spotify.search_track(rec["name"], rec["artist"])
            if result == "RATE_LIMITED":
                print("  Ainda bloqueado. Pulando restante das buscas.")
                break
        if not result:
            print(f"  [{i}/{len(recommendations)}] [--] {rec['name']} - {rec['artist']}")
        elif result["uri"] in seen_uris:
            pass
        else:
            seen_uris.add(result["uri"])
            found_tracks.append(result)
            print(f"  [{i}/{len(recommendations)}] [OK] {result['name']} - {result['artist']}")
        time.sleep(SEARCH_DELAY)

    return found_tracks


def build_playlist(spotify: SpotifyClient, user_input: str, destination="new", target_playlist=None):
    print("\nConsultando IA para montar a playlist...")
    genre, recommendations = recommend_songs(user_input)

    if not recommendations:
        print("Erro: IA nao retornou recomendacoes.")
        return None

    print(f"Genero identificado: {genre}")
    print(f"IA sugeriu {len(recommendations)} musicas. Buscando no Spotify...\n")
    found_tracks = _search_tracks(spotify, recommendations)

    if not found_tracks:
        print("\nNenhuma musica encontrada no Spotify.")
        return None

    if len(found_tracks) < MIN_TRACKS:
        print(f"\nApenas {len(found_tracks)} musica(s) encontrada(s). Minimo necessario: {MIN_TRACKS}.")
        print("Provavelmente o Spotify esta com rate limit. Tente novamente em alguns minutos.")
        return None

    print(f"\n{len(found_tracks)} musicas encontradas!")
    track_uris = [t["uri"] for t in found_tracks]

    if destination == "existing" and target_playlist:
        print(f"Adicionando {len(found_tracks)} musicas em '{target_playlist['name']}'...")
        spotify.add_to_playlist(target_playlist["id"], track_uris)
        print(f"\nPronto! Musicas adicionadas. {target_playlist['url']}")
        return target_playlist["url"]

    title = f"DJ Waguinho - {genre}" if genre else "DJ Waguinho"
    print(f"Gerando capa da playlist...")
    cover = generate_cover(genre, title)

    print(f"Criando playlist '{title}' com {len(found_tracks)} musicas...")
    url = spotify.create_playlist(title, track_uris, cover_base64=cover)
    print(f"\nPlaylist criada! {url}")
    return url
