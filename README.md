# 🎵 SpotifyBot

<p align="center">
  <img src="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green.png" width="200" alt="Spotify Logo"/>
</p>

<p align="center">
  <strong>Bot inteligente para gerenciar seu Spotify com IA</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Spotify-API-1DB954?style=for-the-badge&logo=spotify&logoColor=white"/>
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white"/>
</p>

---

## O que faz?

| Funcionalidade | Descricao |
|---|---|
| **Limpar curtidas** | Remove todas as musicas curtidas da sua conta Spotify |
| **Playlist inteligente** | Voce descreve 3 musicas e a IA monta uma playlist de 50 musicas do mesmo estilo |

### Como funciona a playlist inteligente

```
Voce diz: "veigh talvez voce precise de mim, hungria preta e hungria amor e fe"

    ↓ IA identifica o genero (rap/trap brasileiro)
    ↓ Sugere 50 musicas do MESMO estilo
    ↓ Busca cada musica no Spotify
    ↓ Cria a playlist na sua conta

Resultado: Playlist criada no seu Spotify!
```

---

## Instalacao

### Pre-requisitos

- Python 3.11+
- Conta no [Spotify Developer](https://developer.spotify.com/dashboard)
- Chave da API [OpenAI](https://platform.openai.com/)

### 1. Clone o repositorio

```bash
git clone https://github.com/wagnerflores11/spotifyBot.git
cd spotifyBot
```

### 2. Instale as dependencias

```bash
pip install -r requirements.txt
```

### 3. Configure o `.env`

Crie um arquivo `.env` na raiz do projeto:

```env
SPOTIFY_CLIENT_ID=seu_client_id
SPOTIFY_CLIENT_SECRET=seu_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
OPENAI_API_KEY=sua_chave_openai
```

### 4. Configure o Spotify Developer

1. Acesse [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Crie um app
3. Em **Redirect URIs**, adicione: `http://127.0.0.1:8888/callback`
4. Copie o **Client ID** e **Client Secret** para o `.env`

---

## Uso

```bash
python bot.py
```

```
Autenticando no Spotify...
Logado como: Wagner

========================================
  SpotifyBot
========================================
1. Remover todas as musicas curtidas
2. Criar playlist inteligente
3. Sair
========================================
Escolha uma opcao:
```

Na primeira execucao, o browser abre para voce autorizar o app no Spotify.

---

## Estrutura do projeto

```
spotifyBot/
├── bot.py                  # CLI principal
├── src/
│   ├── config.py           # Configuracoes e constantes
│   ├── spotify_client.py   # Autenticacao e operacoes Spotify
│   ├── recommender.py      # Recomendacao de musicas via OpenAI
│   └── playlist_builder.py # Orquestracao: IA -> busca -> cria playlist
├── requirements.txt
└── .env                    # Credenciais (nao versionado)
```

---

## Tecnologias

<p align="center">
  <img src="https://img.shields.io/badge/spotipy-SDK_Spotify-1DB954?style=flat-square&logo=spotify&logoColor=white"/>
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=flat-square&logo=openai&logoColor=white"/>
  <img src="https://img.shields.io/badge/python--dotenv-Env_Config-ECD53F?style=flat-square&logo=python&logoColor=black"/>
</p>

---

## Licenca

Este projeto e de uso pessoal.
