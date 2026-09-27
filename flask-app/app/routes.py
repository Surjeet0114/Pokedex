from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from .services import java_api, pokeapi
main_bp = Blueprint('main', __name__)

def logged_in():
    return 'access_token' in session

@main_bp.get('/')
def home():
    return render_template('index.html', user=session.get('user'))

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            r = java_api.register(request.form.get('username', ''), request.form.get('email', ''), request.form.get('password', ''))
            session['access_token'] = r['token']
            session['user'] = r['user']
            flash('Account created successfully.', 'success')
            return redirect(url_for('main.home'))
        except java_api.JavaApiError as e:
            return render_template('register.html', error=str(e))
    return render_template('register.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            r = java_api.login(request.form.get('username', ''), request.form.get('password', ''))
            session['access_token'] = r['token']
            session['user'] = r['user']
            return redirect(url_for('main.home'))
        except java_api.JavaApiError as e:
            return render_template('login.html', error=str(e)), 400
    return render_template('login.html')

@main_bp.get('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))

@main_bp.post('/search')
def search():
    name = request.form.get('pokemon', '').strip().lower()
    if not name:
        return render_template('index.html', error='Enter a Pokémon name.', user=session.get('user'), query=name), 400
    try:
        data = pokeapi.pokemon(name)
    except pokeapi.PokeApiError as e:
        return render_template('index.html', error=str(e), user=session.get('user'), query=name), 503
    if not data:
        return render_template('index.html', error=f'No Pokémon found for “{name}”. Try a name or Pokédex number.', user=session.get('user'), query=name), 404
    if logged_in():
        try:
            java_api.add_history(data)
        except java_api.JavaApiError:
            flash('Pokémon loaded, but history could not be saved.', 'warning')
    return render_template('result.html', pokemon=data, user=session.get('user'))

@main_bp.route('/compare', methods=['GET', 'POST'])
def compare():
    if request.method == 'POST':
        names = [request.form.get('pokemon1', '').strip(), request.form.get('pokemon2', '').strip()]
        if not all(names):
            return render_template('compare.html', p1=None, p2=None, error='Enter both Pokémon names or numbers.', query1=names[0], query2=names[1], user=session.get('user')), 400
        out = []
        unavailable = False
        for n in names:
            try:
                out.append(pokeapi.pokemon(n))
            except pokeapi.PokeApiError:
                out.append(None)
                unavailable = True
        if unavailable:
            return render_template('compare.html', p1=out[0], p2=out[1], error='PokéAPI is currently unavailable. Please try again shortly.', query1=names[0], query2=names[1], user=session.get('user')), 503
        return render_template('compare.html', p1=out[0], p2=out[1], query1=names[0], query2=names[1], user=session.get('user'))
    return render_template('compare.html', p1=None, p2=None, user=session.get('user'))

@main_bp.get('/history')
def history():
    if not logged_in():
        return redirect(url_for('main.login'))
    try:
        data = java_api.history()
    except java_api.JavaApiError as e:
        flash(str(e), 'danger')
        data = []
    return render_template('history.html', history=data, user=session.get('user'))

@main_bp.get('/favorites')
def favorites():
    if not logged_in():
        return redirect(url_for('main.login'))
    try:
        data = java_api.favorites()
    except java_api.JavaApiError as e:
        flash(str(e), 'danger')
        data = []
    return render_template('favorites.html', favorites=data, user=session.get('user'))

@main_bp.post('/favorites/<int:pokemon_id>')
def favorite(pokemon_id):
    if not logged_in():
        return redirect(url_for('main.login'))
    try:
        if request.form.get('action') == 'remove':
            java_api.remove_favorite(pokemon_id)
            flash('Removed from favorites.', 'success')
        else:
            java_api.add_favorite({'id': pokemon_id, 'name': request.form['name'], 'image_front': request.form.get('sprite')})
            flash('Added to favorites.', 'success')
    except java_api.JavaApiError as e:
        flash(str(e), 'danger')
    referrer = request.referrer
    if referrer and urlsplit(referrer).netloc == request.host:
        return redirect(referrer)
    return redirect(url_for('main.home'))

@main_bp.get('/profile')
def profile():
    if not logged_in():
        return redirect(url_for('main.login'))
    try:
        user = java_api.me()
    except java_api.JavaApiError as e:
        flash(str(e), 'danger')
        user = session.get('user')
    return render_template('profile.html', user=user)
