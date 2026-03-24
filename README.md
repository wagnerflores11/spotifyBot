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
  <img src="https://img.shields.io/badge/asyncio-Busca_Paralela-FF6F00?style=for-the-badge&logo=python&logoColor=white"/>
</p>

---

## O que faz?

| Funcionalidade | Descricao |
|---|---|
| **Criar playlist inteligente** | Descreva 3 musicas e a IA monta uma playlist de 50 musicas do mesmo estilo com capa gerada por DALL-E |
| **Adicionar musicas** | Busca e adiciona musicas especificas em qualquer playlist existente |
| **Detalhes da playlist** | Visualiza todas as faixas de uma playlist |
| **Duplicar playlist** | Clona uma playlist inteira com todas as musicas |
| **Exportar playlist** | Salva a lista de musicas de uma playlist em arquivo .txt |
| **Historico** | Registra localmente cada playlist criada com data, referencias e link |
| **Limpar curtidas** | Remove todas as musicas curtidas da sua conta Spotify |

### Como funciona a playlist inteligente

```
Voce diz: "veigh talvez voce precise de mim, hungria preta e hungria amor e fe"

    ↓ IA identifica o genero (rap/trap brasileiro)
    ↓ Sugere 50 musicas do MESMO estilo
    ↓ Busca paralela no Spotify (asyncio, 5x mais rapido)
    ↓ Gera capa com DALL-E 3
    ↓ Cria a playlist na sua conta

Resultado: Playlist "DJ Waguinho - rap/trap BR" criada no seu Spotify!
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
  1. Criar playlist nova
  2. Adicionar musicas a uma playlist
  3. Minhas playlists
  4. Detalhes de uma playlist
  5. Duplicar playlist
  6. Exportar playlist para .txt
  7. Historico de playlists criadas
  8. Remover todas as musicas curtidas
  9. Sair
========================================
Escolha uma opcao:
```

Na primeira execucao, o browser abre para voce autorizar o app no Spotify.

---

## Estrutura do projeto

```
spotifyBot/
├── bot.py                    # CLI principal com menu interativo
├── src/
│   ├── config.py             # Configuracoes, validacao e logging
│   ├── models.py             # Dataclasses: Track, Playlist, Recommendation
│   ├── exceptions.py         # Excecoes customizadas
│   ├── spotify_client.py     # Autenticacao e operacoes Spotify
│   ├── async_search.py       # Busca paralela com asyncio
│   ├── recommender.py        # Recomendacao de musicas via OpenAI
│   ├── cover_generator.py    # Geracao de capas via DALL-E 3
│   ├── playlist_builder.py   # Orquestracao: IA -> busca -> cria playlist
│   └── history.py            # Historico local e exportacao
├── requirements.txt
├── history.json              # Historico de playlists criadas (gerado automaticamente)
└── .env                      # Credenciais (nao versionado)
```

---

## Tecnologias

<p align="center">
  <img src="https://img.shields.io/badge/spotipy-SDK_Spotify-1DB954?style=flat-square&logo=spotify&logoColor=white"/>
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=flat-square&logo=openai&logoColor=white"/>
  <img src="https://img.shields.io/badge/DALL--E_3-Capas-412991?style=flat-square&logo=openai&logoColor=white"/>
  <img src="https://img.shields.io/badge/asyncio-Busca_Paralela-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/python--dotenv-Env_Config-ECD53F?style=flat-square&logo=python&logoColor=black"/>
  <img src="https://img.shields.io/badge/Pillow-Imagens-3776AB?style=flat-square&logo=python&logoColor=white"/>
</p>

---

## Licenca

Este projeto e de uso pessoal.
