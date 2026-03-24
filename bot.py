"""SpotifyBot — CLI principal."""

import sys
from typing import Optional

from src.config import setup_logging, validate_config
from src.exceptions import ConfigError, SpotifyBotError
from src.history import add_entry, export_playlist_to_txt, get_entries
from src.models import Playlist, Track
from src.playlist_builder import build_playlist
from src.spotify_client import SpotifyClient

MENU_OPTIONS = {
    "1": "Criar playlist nova",
    "2": "Adicionar musicas a uma playlist",
    "3": "Minhas playlists",
    "4": "Detalhes de uma playlist",
    "5": "Duplicar playlist",
    "6": "Exportar playlist para .txt",
    "7": "Historico de playlists criadas",
    "8": "Remover todas as musicas curtidas",
    "9": "Sair",
}


def menu() -> str:
    """Exibe o menu e retorna a opção escolhida."""
    print("\n========================================")
    print("  SpotifyBot")
    print("========================================")
    for key, label in MENU_OPTIONS.items():
        print(f"  {key}. {label}")
    print("========================================")
    return input("Escolha uma opcao: ").strip()


def _ask_songs() -> Optional[str]:
    """Pede músicas de referência ao usuário."""
    print("\nDigite as musicas de referencia separadas por virgula.")
    print("Exemplo: veigh talvez voce precise de mim, hungria amor e fe, orochi liberdade\n")
    user_input = input("Suas musicas: ").strip()
    if not user_input:
        print("Nenhuma musica informada.")
        return None
    return user_input


def _select_playlist(spotify: SpotifyClient) -> Optional[Playlist]:
    """Lista playlists e permite selecionar uma."""
    playlists = spotify.get_my_playlists()
    if not playlists:
        print("\nVoce nao tem nenhuma playlist.")
        return None

    print(f"\nSuas playlists ({len(playlists)}):\n")
    for i, pl in enumerate(playlists, 1):
        print(f"  {i}. {pl.name} ({pl.total} musicas)")

    while True:
        sel = input("\nDigite o numero da playlist (ou 0 para voltar): ").strip()
        if sel == "0":
            return None
        try:
            idx = int(sel) - 1
            if 0 <= idx < len(playlists):
                return playlists[idx]
        except ValueError:
            pass
        print(f"Opcao invalida. Digite um numero de 1 a {len(playlists)}.")


# --- Handlers ---


def handle_create_playlist(spotify: SpotifyClient) -> None:
    """Cria uma nova playlist via IA."""
    user_input = _ask_songs()
    if not user_input:
        return
    url = build_playlist(spotify, user_input, destination="new")
    if url:
        add_entry(
            name=f"DJ Waguinho",
            url=url,
            genre="",
            track_count=0,
            reference_songs=user_input,
        )


def handle_add_to_playlist(spotify: SpotifyClient) -> None:
    """Adiciona músicas específicas a uma playlist existente (sem IA)."""
    print("\nEscolha a playlist onde deseja adicionar musicas:")
    playlist = _select_playlist(spotify)
    if not playlist:
        return

    print(f"\nPlaylist selecionada: {playlist.name}")
    print("\nDigite as musicas que deseja adicionar separadas por virgula.")
    print("Exemplo: back to friends sombr, sweater weather neighbourhood\n")
    user_input = input("Suas musicas: ").strip()
    if not user_input:
        print("Nenhuma musica informada.")
        return

    songs = [s.strip() for s in user_input.split(",") if s.strip()]
    found_tracks: list[Track] = []

    print(f"\nBuscando {len(songs)} musica(s) no Spotify...\n")
    for i, song in enumerate(songs, 1):
        # Tenta separar "artista - musica" ou busca como texto livre
        parts = song.split(" - ", 1)
        if len(parts) == 2:
            result = spotify.search_track(parts[0].strip(), parts[1].strip())
        else:
            result = spotify.search_track(song, "")

        if result:
            found_tracks.append(result)
            print(f"  [{i}/{len(songs)}] [OK] {result.display()}")
        else:
            print(f"  [{i}/{len(songs)}] [--] {song} (nao encontrada)")

    if not found_tracks:
        print("\nNenhuma musica encontrada.")
        return

    track_uris = [t.uri for t in found_tracks]
    spotify.add_to_playlist(playlist.id, track_uris)
    print(f"\nPronto! {len(found_tracks)} musica(s) adicionada(s) em '{playlist.name}'.")


def handle_my_playlists(spotify: SpotifyClient) -> None:
    """Lista todas as playlists do usuário."""
    playlists = spotify.get_my_playlists()
    if not playlists:
        print("\nVoce nao tem nenhuma playlist.")
        return

    print(f"\nSuas playlists ({len(playlists)}):\n")
    for i, pl in enumerate(playlists, 1):
        print(f"  {i}. {pl.name} ({pl.total} musicas)")
        print(f"     {pl.url}")


def handle_playlist_details(spotify: SpotifyClient) -> None:
    """Mostra as faixas de uma playlist."""
    print("\nEscolha uma playlist para ver os detalhes:")
    playlist = _select_playlist(spotify)
    if not playlist:
        return

    tracks = spotify.get_playlist_tracks(playlist.id)
    print(f"\n{playlist.name} ({len(tracks)} musicas):\n")
    for i, track in enumerate(tracks, 1):
        print(f"  {i}. {track.display()}")


def handle_duplicate_playlist(spotify: SpotifyClient) -> None:
    """Duplica uma playlist existente."""
    print("\nEscolha a playlist que deseja duplicar:")
    playlist = _select_playlist(spotify)
    if not playlist:
        return

    new_name = input(f"\nNome da copia (Enter para '{playlist.name} (copia)'): ").strip()
    print("Duplicando playlist...")
    url = spotify.duplicate_playlist(playlist, new_name=new_name or None)
    if url:
        print(f"\nPlaylist duplicada! {url}")
    else:
        print("\nNao foi possivel duplicar (playlist vazia?).")


def handle_export_playlist(spotify: SpotifyClient) -> None:
    """Exporta as faixas de uma playlist para um arquivo .txt."""
    print("\nEscolha a playlist para exportar:")
    playlist = _select_playlist(spotify)
    if not playlist:
        return

    tracks = spotify.get_playlist_tracks(playlist.id)
    if not tracks:
        print("\nPlaylist vazia, nada para exportar.")
        return

    safe_name = playlist.name.replace("/", "-").replace("\\", "-")
    filename = f"{safe_name}.txt"
    path = export_playlist_to_txt(tracks, playlist.name, filename)
    print(f"\nPlaylist exportada para: {path}")


def handle_history(_spotify: SpotifyClient) -> None:
    """Mostra o histórico de playlists criadas pelo bot."""
    entries = get_entries()
    if not entries:
        print("\nNenhuma playlist no historico ainda.")
        return

    print(f"\nHistorico ({len(entries)} playlists criadas):\n")
    for i, entry in enumerate(entries, 1):
        date = entry.get("created_at", "")[:10]
        print(f"  {i}. {entry['name']} ({date})")
        print(f"     Referencia: {entry.get('reference_songs', '-')}")
        print(f"     {entry.get('url', '')}")


def handle_remove_likes(spotify: SpotifyClient) -> None:
    """Remove todas as músicas curtidas (com confirmação)."""
    confirm = input("\nTem certeza que deseja remover TODAS as musicas curtidas? (sim/nao): ").strip().lower()
    if confirm != "sim":
        print("Operacao cancelada.")
        return
    print("Removendo musicas curtidas...")
    total = spotify.remove_all_liked_songs()
    print(f"\nPronto! {total} musicas removidas.")


# --- Main ---

ACTIONS = {
    "1": handle_create_playlist,
    "2": handle_add_to_playlist,
    "3": handle_my_playlists,
    "4": handle_playlist_details,
    "5": handle_duplicate_playlist,
    "6": handle_export_playlist,
    "7": handle_history,
    "8": handle_remove_likes,
}


def main() -> None:
    """Ponto de entrada do SpotifyBot."""
    setup_logging()

    missing = validate_config()
    if missing:
        print(f"Erro: variaveis de ambiente faltando: {', '.join(missing)}")
        print("Configure o arquivo .env e tente novamente.")
        sys.exit(1)

    print("Autenticando no Spotify...")
    try:
        spotify = SpotifyClient()
    except SpotifyBotError as exc:
        print(f"Erro: {exc}")
        sys.exit(1)

    print(f"Logado como: {spotify.get_username()}")

    while True:
        choice = menu()
        if choice == "9":
            print("Ate mais!")
            break

        action = ACTIONS.get(choice)
        if action:
            try:
                action(spotify)
            except SpotifyBotError as exc:
                print(f"\nErro: {exc}")
            except KeyboardInterrupt:
                print("\nOperacao cancelada.")
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    main()
