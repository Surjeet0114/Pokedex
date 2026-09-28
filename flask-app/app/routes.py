from __future__ import annotations

from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .services import java_api, pokeapi

main_bp = Blueprint("main", __name__)


def logged_in() -> bool:
    return "access_token" in session


def _store_authentication(response: dict) -> None:
    token = response.get("token")
    user = response.get("user")
    if not token or not isinstance(user, dict):
        raise java_api.JavaApiError("Java backend returned an invalid sign-in response.")

    # Discard the previous session contents before storing the new identity.
    session.clear()
    session["access_token"] = token
    session["user"] = user


def _safe_referrer() -> str | None:
    referrer = request.referrer
    if not referrer:
        return None

    parts = urlsplit(referrer)
    if parts.scheme in {"http", "https"} and parts.netloc == request.host:
        return referrer
    return None


def _expire_local_session(error: java_api.JavaApiError) -> None:
    if error.status_code == 401:
        session.clear()


@main_bp.get("/")
def home():
    return render_template("index.html", user=session.get("user"))


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", user=session.get("user"))

    try:
        response = java_api.register(
            request.form.get("username", ""),
            request.form.get("email", ""),
            request.form.get("password", ""),
        )
        _store_authentication(response)
    except java_api.JavaApiError as error:
        return render_template(
            "register.html", error=str(error), user=session.get("user")
        ), error.status_code

    flash("Account created successfully.", "success")
    return redirect(url_for("main.home"))


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", user=session.get("user"))

    try:
        response = java_api.login(
            request.form.get("username", ""), request.form.get("password", "")
        )
        _store_authentication(response)
    except java_api.JavaApiError as error:
        return render_template("login.html", error=str(error), user=session.get("user")), error.status_code

    flash("Welcome back.", "success")
    return redirect(url_for("main.home"))


@main_bp.post("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.home"))


@main_bp.post("/search")
def search():
    name = request.form.get("pokemon", "").strip().lower()
    if not name:
        return render_template(
            "index.html",
            error="Enter a Pokémon name or Pokédex number.",
            user=session.get("user"),
            query=name,
        ), 400

    try:
        pokemon = pokeapi.pokemon(name)
    except pokeapi.PokeApiError as error:
        return render_template(
            "index.html", error=str(error), user=session.get("user"), query=name
        ), 503

    if not pokemon:
        return render_template(
            "index.html",
            error=f'No Pokémon found for “{name}”. Try a name or Pokédex number.',
            user=session.get("user"),
            query=name,
        ), 404

    if logged_in():
        try:
            java_api.add_history(pokemon)
        except java_api.JavaApiError:
            flash("Pokémon loaded, but search history could not be saved.", "warning")

    return render_template("result.html", pokemon=pokemon, user=session.get("user"))


@main_bp.route("/compare", methods=["GET", "POST"])
def compare():
    if request.method == "GET":
        return render_template("compare.html", p1=None, p2=None, user=session.get("user"))

    names = [request.form.get("pokemon1", "").strip(), request.form.get("pokemon2", "").strip()]
    if not all(names):
        return render_template(
            "compare.html",
            p1=None,
            p2=None,
            error="Enter both Pokémon names or numbers.",
            query1=names[0],
            query2=names[1],
            user=session.get("user"),
        ), 400

    results = []
    unavailable = False
    for name in names:
        try:
            results.append(pokeapi.pokemon(name))
        except pokeapi.PokeApiError:
            results.append(None)
            unavailable = True

    if unavailable:
        error = "PokéAPI is currently unavailable. Please try again shortly."
        status_code = 503
    else:
        error = None
        status_code = 200

    return render_template(
        "compare.html",
        p1=results[0],
        p2=results[1],
        error=error,
        query1=names[0],
        query2=names[1],
        user=session.get("user"),
    ), status_code


@main_bp.get("/history")
def history():
    if not logged_in():
        return redirect(url_for("main.login"))

    try:
        entries = java_api.history()
    except java_api.JavaApiError as error:
        _expire_local_session(error)
        flash(str(error), "danger")
        entries = []
    return render_template("history.html", history=entries, user=session.get("user"))


@main_bp.get("/favorites")
def favorites():
    if not logged_in():
        return redirect(url_for("main.login"))

    try:
        entries = java_api.favorites()
    except java_api.JavaApiError as error:
        _expire_local_session(error)
        flash(str(error), "danger")
        entries = []
    return render_template("favorites.html", favorites=entries, user=session.get("user"))


@main_bp.post("/favorites/<int:pokemon_id>")
def favorite(pokemon_id: int):
    if not logged_in():
        return redirect(url_for("main.login"))

    if pokemon_id <= 0:
        flash("Pokédex numbers must be positive.", "danger")
        return redirect(url_for("main.home"))

    try:
        if request.form.get("action") == "remove":
            java_api.remove_favorite(pokemon_id)
            flash("Removed from favorites.", "success")
        else:
            name = request.form.get("name", "").strip()
            if not name:
                flash("Could not save this favorite. Please search for it again.", "danger")
                return redirect(url_for("main.home"))
            java_api.add_favorite(
                {
                    "id": pokemon_id,
                    "name": name,
                    "image_front": request.form.get("sprite"),
                }
            )
            flash("Added to favorites.", "success")
    except java_api.JavaApiError as error:
        _expire_local_session(error)
        flash(str(error), "danger")

    return redirect(_safe_referrer() or url_for("main.home"))


@main_bp.get("/profile")
def profile():
    if not logged_in():
        return redirect(url_for("main.login"))

    try:
        user = java_api.me()
    except java_api.JavaApiError as error:
        _expire_local_session(error)
        flash(str(error), "danger")
        user = session.get("user")
    return render_template("profile.html", user=user)
