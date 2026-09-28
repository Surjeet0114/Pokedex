from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

import requests

BASE_URL = "https://pokeapi.co/api/v2"
TIMEOUT = 10
DETAIL_WORKERS = 8


class PokeApiError(Exception):
    """Raised when PokéAPI cannot be reached or returns invalid data."""


def get_json(url: str) -> dict[str, Any] | None:
    try:
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        raise PokeApiError("PokéAPI is currently unavailable.") from error


def _move_details(item: dict[str, Any]) -> dict[str, Any] | None:
    move = get_json(item["move"]["url"])
    if not move:
        return None

    damage_type = move.get("type") or {}
    damage_class = move.get("damage_class") or {}
    return {
        "name": move["name"],
        "type": damage_type.get("name"),
        "power": move.get("power"),
        "pp": move.get("pp"),
        "accuracy": move.get("accuracy"),
        "class": damage_class.get("name"),
    }


def _ability_details(item: dict[str, Any]) -> dict[str, str]:
    ability = get_json(item["ability"]["url"])
    description = "No description available"
    if ability:
        for entry in ability.get("effect_entries", []):
            if entry.get("language", {}).get("name") == "en":
                description = entry.get("short_effect") or description
                break

    return {"name": item["ability"]["name"], "description": description}


def pokemon(name: str) -> dict[str, Any] | None:
    normalized_name = (name or "").strip().lower()
    if not normalized_name:
        return None

    data = get_json(f"{BASE_URL}/pokemon/{normalized_name}")
    if not data:
        return None

    species = get_json(data["species"]["url"])
    evolution = []
    if species and species.get("evolution_chain"):
        evolution = get_evolution_chain(species["evolution_chain"]["url"])

    ability_items = data.get("abilities", [])
    move_items = data.get("moves", [])[:10]
    with ThreadPoolExecutor(max_workers=DETAIL_WORKERS) as executor:
        ability_futures = [
            executor.submit(_ability_details, item) for item in ability_items
        ]
        move_futures = [executor.submit(_move_details, item) for item in move_items]
        abilities = [future.result() for future in ability_futures]
        moves = [future.result() for future in move_futures]

    sprites = data.get("sprites") or {}
    artwork = sprites.get("other") or {}
    official_artwork = artwork.get("official-artwork") or {}
    habitat = (species or {}).get("habitat") or {}
    color = (species or {}).get("color") or {}

    return {
        "name": data["name"].replace("-", " ").title(),
        "id": data["id"],
        "types": [entry["type"]["name"] for entry in data.get("types", [])],
        "height": data.get("height", 0),
        "weight": data.get("weight", 0),
        "image_front": sprites.get("front_default"),
        "image_back": sprites.get("back_default"),
        "image_hd": official_artwork.get("front_default"),
        "stats": {
            entry["stat"]["name"]: entry["base_stat"]
            for entry in data.get("stats", [])
        },
        "moves": [move for move in moves if move],
        "color": color.get("name", "Unknown"),
        "habitat": habitat.get("name", "Unknown"),
        "evolution": evolution,
        "abilities": abilities,
        "cry": (data.get("cries") or {}).get("latest"),
    }


def get_evolution_chain(url: str) -> list[list[dict[str, str]]]:
    data = get_json(url)
    if not data:
        return []

    result: list[list[dict[str, str]]] = []
    current_stage = [data["chain"]]
    while current_stage:
        stage = []
        next_stage = []
        for node in current_stage:
            species = node["species"]
            species_url = species.get("url", "").rstrip("/")
            pokemon_id = species_url.rsplit("/", maxsplit=1)[-1]
            stage.append(
                {
                    "name": species["name"].replace("-", " "),
                    "sprite": (
                        "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
                        f"sprites/pokemon/{pokemon_id}.png"
                    ),
                }
            )
            next_stage.extend(node.get("evolves_to", []))
        result.append(stage)
        current_stage = next_stage
    return result
