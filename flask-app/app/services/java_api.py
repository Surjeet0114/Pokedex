import requests
from flask import current_app, session

class JavaApiError(Exception):
    pass

def _request(method, path, **kwargs):
    url = current_app.config['JAVA_API_URL'].rstrip('/') + path
    headers = kwargs.pop('headers', {})
    token = session.get('access_token')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        r = requests.request(method, url, headers=headers, timeout=8, **kwargs)
        if r.status_code >= 400:
            try:
                detail = r.json().get('message', 'Request failed')
            except ValueError:
                detail = 'Request failed'
            raise JavaApiError(detail)
        return r.json() if r.content else {}
    except requests.RequestException as e:
        raise JavaApiError('Java backend is unavailable.') from e

def register(username, email, password):
    return _request('POST', '/api/auth/register', json={'username': username, 'email': email, 'password': password})

def login(username, password):
    return _request('POST', '/api/auth/login', json={'username': username, 'password': password})

def me():
    return _request('GET', '/api/users/me')

def add_history(p):
    return _request('POST', '/api/users/history', json={'pokemonId': p['id'], 'pokemonName': p['name'], 'types': ','.join(p['types'])})

def history():
    return _request('GET', '/api/users/history')

def favorites():
    return _request('GET', '/api/users/favorites')

def add_favorite(p):
    return _request('POST', '/api/users/favorites', json={'pokemonId': p['id'], 'pokemonName': p['name'], 'spriteUrl': p.get('image_front')})

def remove_favorite(pid):
    return _request('DELETE', f'/api/users/favorites/{pid}')
