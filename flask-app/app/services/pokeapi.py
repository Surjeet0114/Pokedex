from concurrent.futures import ThreadPoolExecutor

import requests
BASE_URL = 'https://pokeapi.co/api/v2'
TIMEOUT = 10
DETAIL_WORKERS = 8

class PokeApiError(Exception):
    pass

def get_json(url):
    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise PokeApiError('PokéAPI is currently unavailable.') from e

def _move_details(item):
    move = get_json(item['move']['url'])
    if not move:
        return None
    return {'name': move['name'], 'type': (move.get('type') or {}).get('name'), 'power': move.get('power'), 'pp': move.get('pp'), 'accuracy': move.get('accuracy'), 'class': (move.get('damage_class') or {}).get('name')}


def _ability_details(item):
    ability = get_json(item['ability']['url'])
    description = 'No description available'
    if ability:
        for entry in ability.get('effect_entries', []):
            if entry.get('language', {}).get('name') == 'en':
                description = entry.get('short_effect') or description
                break
    return {'name': item['ability']['name'], 'description': description}


def pokemon(name):
    name = (name or '').strip().lower()
    if not name:
        return None
    data = get_json(f'{BASE_URL}/pokemon/{name}')
    if not data:
        return None
    species = get_json(data['species']['url'])
    evo = get_evolution_chain(species['evolution_chain']['url']) if species else []
    # Fetch the displayed move and ability metadata concurrently to avoid a long
    # chain of sequential requests for a single Pokédex lookup.
    ability_items = data.get('abilities', [])
    move_items = data.get('moves', [])[:10]
    with ThreadPoolExecutor(max_workers=DETAIL_WORKERS) as pool:
        abilities = list(pool.map(_ability_details, ability_items))
        moves = [move for move in pool.map(_move_details, move_items) if move]
    sprites = data.get('sprites') or {}
    return {'name': data['name'].replace('-', ' ').title(), 'id': data['id'], 'types': [x['type']['name'] for x in data.get('types', [])], 'height': data.get('height', 0), 'weight': data.get('weight', 0), 'image_front': sprites.get('front_default'), 'image_back': sprites.get('back_default'), 'image_hd': (sprites.get('other') or {}).get('official-artwork', {}).get('front_default'), 'stats': {x['stat']['name']: x['base_stat'] for x in data.get('stats', [])}, 'moves': moves, 'color': (species.get('color') or {}).get('name', 'Unknown') if species else 'Unknown', 'habitat': (species.get('habitat') or {}).get('name', 'Unknown') if species else 'Unknown', 'evolution': evo, 'abilities': abilities, 'cry': (data.get('cries') or {}).get('latest')}

def get_evolution_chain(url):
    data = get_json(url)
    if not data:
        return []
    result = []
    node = data['chain']
    while node:
        name = node['species']['name']
        result.append({'name': name.replace('-', ' '), 'sprite': f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{node["species"].get("url", "").rstrip("/").split("/")[-1]}.png'})
        if not node.get('evolves_to'):
            break
        node = node['evolves_to'][0]
    return result
