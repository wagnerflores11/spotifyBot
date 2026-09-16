"""Exceções customizadas do SpotifyBot."""


class SpotifyBotError(Exception):
    """Erro base do SpotifyBot."""


class RateLimitError(SpotifyBotError):
    """Spotify retornou 429 (rate limit)."""

    def __init__(self, message: str = "Rate limit do Spotify atingido"):
        super().__init__(message)


class AuthenticationError(SpotifyBotError):
    """Falha na autenticação com o Spotify."""

    def __init__(self, message: str = "Falha na autenticacao com o Spotify"):
        super().__init__(message)


class AIError(SpotifyBotError):
    """Erro na comunicação com a API de IA."""

    def __init__(self, message: str = "Erro ao consultar a IA"):
        super().__init__(message)
