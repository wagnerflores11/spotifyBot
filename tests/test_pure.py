"""Testes das funções puras — sem rede, sem credenciais."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import BuildResult, Playlist, Recommendation, Track
from src.recommender import _fix_truncated_json, _parse_response, _song_key


# --- models.Playlist.count_label / display ---

def test_count_label_desconhecido():
    assert Playlist(id="x", name="Sem contagem").count_label == ""


def test_count_label_zero_e_conhecido():
    # 0 é uma contagem real (playlist vazia), diferente de desconhecido (None)
    assert Playlist(id="x", name="Vazia", total=0).count_label == " (0 musicas)"


def test_count_label_com_numero():
    assert Playlist(id="x", name="Cheia", total=22).count_label == " (22 musicas)"


def test_display_com_e_sem_indice():
    p = Playlist(id="x", name="Minha", total=3)
    assert p.display() == "Minha (3 musicas)"
    assert p.display(2) == "  2. Minha (3 musicas)"


def test_display_sem_contagem_nao_mostra_zero():
    p = Playlist(id="x", name="Sem info")
    assert "musicas" not in p.display(1)


# --- models auxiliares ---

def test_track_display():
    assert Track(uri="u", name="Song", artist="Artist").display() == "Song - Artist"


def test_recommendation_is_empty():
    assert Recommendation(genre="pop").is_empty
    assert not Recommendation(genre="pop", songs=[{"name": "a", "artist": "b"}]).is_empty


def test_build_result_campos():
    r = BuildResult(url="http://x", title="T", genre="pop", track_count=5)
    assert (r.url, r.title, r.genre, r.track_count) == ("http://x", "T", "pop", 5)


# --- recommender._song_key ---

def test_song_key_normaliza_caixa_e_espaco():
    a = {"name": " Blinding Lights ", "artist": "The Weeknd"}
    b = {"name": "blinding lights", "artist": "the weeknd"}
    assert _song_key(a) == _song_key(b)


def test_song_key_diferencia_musicas():
    a = {"name": "A", "artist": "X"}
    b = {"name": "B", "artist": "X"}
    assert _song_key(a) != _song_key(b)


# --- recommender._parse_response ---

def test_parse_response_valido():
    raw = '{"genre": "pop", "songs": [{"name": "A", "artist": "X"}, {"name": "B", "artist": "Y"}]}'
    rec = _parse_response(raw)
    assert rec.genre == "pop"
    assert len(rec.songs) == 2


def test_parse_response_deduplica():
    raw = '{"genre": "pop", "songs": [{"name": "A", "artist": "X"}, {"name": "a", "artist": "x"}]}'
    rec = _parse_response(raw)
    assert len(rec.songs) == 1


def test_parse_response_vazio():
    assert _parse_response("").is_empty


def test_parse_response_json_invalido_sem_crash():
    # não deve levantar exceção, retorna recomendação vazia
    assert _parse_response("isso nao e json").is_empty


# --- recommender._fix_truncated_json / recuperação end-to-end ---

def test_parse_response_recupera_json_com_texto_extra():
    # LLM devolve JSON válido seguido de texto — json.loads falha e o
    # fallback de reparo deve recuperar as músicas.
    raw = (
        '{"genre": "pop", "songs": '
        '[{"name": "A", "artist": "X"}, {"name": "B", "artist": "Y"}]}'
        "\n\nEspero que ajude!"
    )
    rec = _parse_response(raw)
    assert rec.genre == "pop"
    assert [s["name"] for s in rec.songs] == ["A", "B"]


def test_fix_truncated_json_sem_fechamento_retorna_json_valido():
    import json
    fixed = _fix_truncated_json("lixo sem chave")
    assert json.loads(fixed) == {"genre": "", "songs": []}
