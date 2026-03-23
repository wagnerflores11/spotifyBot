from src.spotify_client import SpotifyClient
from src.recommender import recommend_songs


def build_playlist(spotify: SpotifyClient, user_input: str):
    print("\nConsultando IA para montar a playlist...")
    recommendations = recommend_songs(user_input)

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

    artists = ", ".join(dict.fromkeys(t["artist"] for t in found_tracks[:3]))
    playlist_name = f"SpotifyBot: {artists} e mais"
    track_uris = [t["uri"] for t in found_tracks]

    print(f"\nCriando playlist '{playlist_name}' com {len(found_tracks)} musicas...")
    url = spotify.create_playlist(playlist_name, track_uris)
    print(f"\nPlaylist criada! {url}")
    return url
