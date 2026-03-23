from src.spotify_client import SpotifyClient
from src.recommender import recommend_songs
from src.cover_generator import generate_cover


def build_playlist(spotify: SpotifyClient, user_input: str):
    print("\nConsultando IA para montar a playlist...")
    genre, recommendations = recommend_songs(user_input)

    if not recommendations:
        print("Erro: IA nao retornou recomendacoes.")
        return None

    print(f"IA sugeriu {len(recommendations)} musicas. Buscando no Spotify...\n")

    found_tracks = []
    seen_uris = set()

    for rec in recommendations:
        result = spotify.search_track(rec["name"], rec["artist"])
        if not result:
            print(f"  [--] {rec['name']} - {rec['artist']} (nao encontrada)")
            continue
        if result["uri"] in seen_uris:
            continue
        seen_uris.add(result["uri"])
        found_tracks.append(result)
        print(f"  [OK] {result['name']} - {result['artist']}")

    if not found_tracks:
        print("\nNenhuma musica encontrada no Spotify.")
        return None

    title = f"DJ Waguinho - {genre}" if genre else "DJ Waguinho"

    print(f"\nGerando capa da playlist...")
    cover = generate_cover(genre, title)

    track_uris = [t["uri"] for t in found_tracks]
    print(f"Criando playlist '{title}' com {len(found_tracks)} musicas...")
    url = spotify.create_playlist(title, track_uris, cover_base64=cover)
    print(f"\nPlaylist criada! {url}")
    return url
