from src.spotify_client import SpotifyClient
from src.playlist_builder import build_playlist


def menu():
    print("\n========================================")
    print("  SpotifyBot")
    print("========================================")
    print("1. Criar playlist nova")
    print("2. Adicionar musicas a uma playlist")
    print("3. Minhas playlists")
    print("4. Remover todas as musicas curtidas")
    print("5. Sair")
    print("========================================")
    return input("Escolha uma opcao: ").strip()


def _ask_songs():
    print("\nDigite as musicas de referencia separadas por virgula.")
    print("Exemplo: veigh talvez voce precise de mim, hungria amor e fe, orochi liberdade\n")
    user_input = input("Suas musicas: ").strip()
    if not user_input:
        print("Nenhuma musica informada.")
        return None
    return user_input


def _select_playlist(spotify):
    playlists = spotify.get_my_playlists()
    if not playlists:
        print("\nVoce nao tem nenhuma playlist.")
        return None

    print(f"\nSuas playlists ({len(playlists)}):\n")
    for i, pl in enumerate(playlists, 1):
        print(f"  {i}. {pl['name']} ({pl['total']} musicas)")

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


def handle_create_playlist(spotify):
    user_input = _ask_songs()
    if not user_input:
        return
    build_playlist(spotify, user_input, destination="new")


def handle_add_to_playlist(spotify):
    print("\nEscolha a playlist onde deseja adicionar musicas:")
    playlist = _select_playlist(spotify)
    if not playlist:
        return

    print(f"\nPlaylist selecionada: {playlist['name']}")
    user_input = _ask_songs()
    if not user_input:
        return
    build_playlist(spotify, user_input, destination="existing", target_playlist=playlist)


def handle_my_playlists(spotify):
    playlists = spotify.get_my_playlists()
    if not playlists:
        print("\nVoce nao tem nenhuma playlist.")
        return

    print(f"\nSuas playlists ({len(playlists)}):\n")
    for i, pl in enumerate(playlists, 1):
        print(f"  {i}. {pl['name']} ({pl['total']} musicas)")
        print(f"     {pl['url']}")

    print("\nDeseja adicionar musicas a alguma playlist?")
    resp = input("Digite o numero da playlist (ou Enter para voltar): ").strip()
    if not resp:
        return

    try:
        idx = int(resp) - 1
        if 0 <= idx < len(playlists):
            playlist = playlists[idx]
            print(f"\nPlaylist selecionada: {playlist['name']}")
            user_input = _ask_songs()
            if not user_input:
                return
            build_playlist(spotify, user_input, destination="existing", target_playlist=playlist)
            return
    except ValueError:
        pass
    print("Opcao invalida.")


def handle_remove_likes(spotify):
    confirm = input("\nTem certeza que deseja remover TODAS as musicas curtidas? (sim/nao): ").strip().lower()
    if confirm != "sim":
        print("Operacao cancelada.")
        return
    print("Removendo musicas curtidas...")
    total = spotify.remove_all_liked_songs()
    print(f"\nPronto! {total} musicas removidas.")


def main():
    print("Autenticando no Spotify...")
    spotify = SpotifyClient()
    print(f"Logado como: {spotify.get_username()}")

    actions = {
        "1": handle_create_playlist,
        "2": handle_add_to_playlist,
        "3": handle_my_playlists,
        "4": handle_remove_likes,
    }

    while True:
        choice = menu()
        if choice == "5":
            print("Ate mais!")
            break
        action = actions.get(choice)
        if action:
            action(spotify)
        else:
            print("Opcao invalida. Digite um numero de 1 a 5.")


if __name__ == "__main__":
    main()
