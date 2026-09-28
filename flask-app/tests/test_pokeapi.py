from __future__ import annotations

import requests
import pytest

from app.services import pokeapi


def test_search_rejects_blank_names_without_api_request(monkeypatch):
    def unexpected_request(url, timeout):
        raise AssertionError("A blank search should not call PokéAPI.")

    monkeypatch.setattr(pokeapi.requests, "get", unexpected_request)

    assert pokeapi.pokemon("  ") is None


def test_evolution_chain_preserves_branched_stages(monkeypatch):
    monkeypatch.setattr(
        pokeapi,
        "get_json",
        lambda url: {
            "chain": {
                "species": {"name": "eevee", "url": "https://pokeapi.co/api/v2/pokemon-species/133/"},
                "evolves_to": [
                    {
                        "species": {"name": "vaporeon", "url": "https://pokeapi.co/api/v2/pokemon-species/134/"},
                        "evolves_to": [],
                    },
                    {
                        "species": {"name": "jolteon", "url": "https://pokeapi.co/api/v2/pokemon-species/135/"},
                        "evolves_to": [],
                    },
                ],
            }
        },
    )

    result = pokeapi.get_evolution_chain("https://pokeapi.co/api/v2/evolution-chain/67/")

    assert [entry["name"] for entry in result[0]] == ["eevee"]
    assert [entry["name"] for entry in result[1]] == ["vaporeon", "jolteon"]
    assert result[1][0]["sprite"].endswith("/134.png")


def test_pokemon_details_combine_api_data(monkeypatch):
    pokemon_data = {
        "name": "pikachu",
        "id": 25,
        "species": {"url": "species-url"},
        "types": [{"type": {"name": "electric"}}],
        "height": 4,
        "weight": 60,
        "sprites": {
            "front_default": "front.png",
            "back_default": "back.png",
            "other": {"official-artwork": {"front_default": "art.png"}},
        },
        "stats": [{"stat": {"name": "hp"}, "base_stat": 35}],
        "moves": [{"move": {"name": "thunder-shock", "url": "move-url"}}],
        "abilities": [{"ability": {"name": "static", "url": "ability-url"}}],
        "cries": {"latest": "cry.ogg"},
    }
    species_data = {
        "color": {"name": "yellow"},
        "habitat": {"name": "forest"},
        "evolution_chain": {"url": "chain-url"},
    }
    monkeypatch.setattr(
        pokeapi,
        "get_json",
        lambda url: {
            f"{pokeapi.BASE_URL}/pokemon/pikachu": pokemon_data,
            "species-url": species_data,
            "chain-url": {"chain": {"species": {"name": "pichu", "url": "species/172/"}, "evolves_to": []}},
        }.get(url),
    )
    monkeypatch.setattr(
        pokeapi,
        "_move_details",
        lambda item: {"name": item["move"]["name"], "power": 40},
    )
    monkeypatch.setattr(
        pokeapi,
        "_ability_details",
        lambda item: {"name": item["ability"]["name"], "description": "Static"},
    )

    result = pokeapi.pokemon(" Pikachu ")

    assert result["name"] == "Pikachu"
    assert result["types"] == ["electric"]
    assert result["stats"] == {"hp": 35}
    assert result["moves"][0]["name"] == "thunder-shock"
    assert result["abilities"][0]["name"] == "static"
    assert result["evolution"][0][0]["name"] == "pichu"
    assert result["image_hd"] == "art.png"


def test_network_failures_are_reported_as_pokeapi_errors(monkeypatch):
    def unavailable(url, timeout):
        raise requests.Timeout("internal network detail")

    monkeypatch.setattr(pokeapi.requests, "get", unavailable)

    with pytest.raises(pokeapi.PokeApiError, match="PokéAPI is currently unavailable"):
        pokeapi.get_json("https://pokeapi.co/api/v2/pokemon/pikachu")
