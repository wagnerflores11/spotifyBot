from src.spotify_client import SpotifyClient
from src.playlist_builder import build_playlist


def menu():
    print("\n========================================")
    print("  SpotifyBot")
    print("========================================")
    print("1. Remover todas as musicas curtidas")
    print("2. Criar playlist inteligente")
    print("3. Sair")
    print("========================================")
    return input("Escolha uma opcao: ").strip()


def handle_remove_likes(spotify):
    confirm = input("\nTem certeza que deseja remover TODAS as musicas curtidas? (sim/nao): ").strip().lower()
    if confirm != "sim":
        print("Operacao cancelada.")
        return
    print("Removendo musicas curtidas...")
    total = spotify.remove_all_liked_songs()
    print(f"\nPronto! {total} musicas removidas.")


def handle_create_playlist(spotify):
    print("\nDescreva 3 musicas (ex: 'veigh talvez voce precise de mim, hungria preta e hungria amor e fe')")
    user_input = input("\nSuas 3 musicas: ").strip()
    if not user_input:
        print("Nenhuma musica informada.")
        return
    build_playlist(spotify, user_input)


def main():
    print("Autenticando no Spotify...")
    spotify = SpotifyClient()
    print(f"Logado como: {spotify.get_username()}")

    actions = {
        "1": handle_remove_likes,
        "2": handle_create_playlist,
    }

    while True:
        choice = menu()
        if choice == "3":
            print("Ate mais!")
            break
        action = actions.get(choice)
        if action:
            action(spotify)
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    main()
