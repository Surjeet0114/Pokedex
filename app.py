from flask import Flask, render_template, request
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "pokedex.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            poke_id INTEGER,
            types TEXT,
            search_date TEXT,
            search_time TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_history(name, poke_id, types):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    cur.execute(
        "INSERT INTO history (name, poke_id, types, search_date, search_time) VALUES (?,?,?,?,?)",
        (name, poke_id, ",".join(types), date, time)
    )
    conn.commit()
    conn.close()


def get_json(url):
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None


def get_move_details(url):
    data = get_json(url)
    if not data:
        return None

    return {
        "name": data["name"],
        "type": data["type"]["name"],
        "power": data["power"],
        "pp": data["pp"],
        "accuracy": data["accuracy"],
        "class": data["damage_class"]["name"]
    }


def get_ability_description(url):
    data = get_json(url)
    if not data:
        return None

    for entry in data["effect_entries"]:
        if entry["language"]["name"] == "en":
            return entry["short_effect"]
    return "No description available"


def get_evolution_chain(url):
    evo_data = get_json(url)
    if not evo_data:
        return []

    chain = []
    node = evo_data["chain"]

    while node:
        name = node["species"]["name"]
        sprite = f"https://img.pokemondb.net/sprites/home/normal/{name}.png"
        chain.append({"name": name, "sprite": sprite})

        if node["evolves_to"]:
            node = node["evolves_to"][0]
        else:
            break

    return chain


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form["pokemon"].lower()
        data = get_json(f"https://pokeapi.co/api/v2/pokemon/{name}")

        if not data:
            return render_template("index.html", error="Pokémon not found")

        types = [t["type"]["name"] for t in data["types"]]
        save_history(data["name"], data["id"], types)

        species = get_json(data["species"]["url"])
        habitat = species["habitat"]["name"] if species and species["habitat"] else "Unknown"
        color = species["color"]["name"] if species else "Unknown"

        evo_chain = get_evolution_chain(species["evolution_chain"]["url"])

        stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}

        moves = []
        for m in data["moves"][:10]:
            moves.append(get_move_details(m["move"]["url"]))

        abilities = []
        for a in data["abilities"]:
            abilities.append({
                "name": a["ability"]["name"],
                "description": get_ability_description(a["ability"]["url"])
            })

        cry = None
        if data.get("cries") and data["cries"].get("latest"):
            cry = data["cries"]["latest"]

        return render_template(
            "result.html",
            name=data["name"].capitalize(),
            poke_id=data["id"],
            types=types,
            height=data["height"],
            weight=data["weight"],
            image_front=data["sprites"]["front_default"],
            image_back=data["sprites"]["back_default"],
            image_hd=data["sprites"]["other"]["official-artwork"]["front_default"],
            stats=stats,
            moves=moves,
            color=color,
            habitat=habitat,
            evolution=evo_chain,
            abilities=abilities,
            cry=cry
        )

    return render_template("index.html")


@app.route("/history")
def history():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name, poke_id, types, search_date, search_time FROM history ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    return render_template("history.html", history=rows)


@app.route("/compare", methods=["GET", "POST"])
def compare():
    if request.method == "POST":
        p1 = request.form["pokemon1"].lower()
        p2 = request.form["pokemon2"].lower()

        def load(p):
            d = get_json(f"https://pokeapi.co/api/v2/pokemon/{p}")
            if not d:
                return None
            return {
                "name": d["name"].capitalize(),
                "sprite": d["sprites"]["front_default"],
                "types": [t["type"]["name"] for t in d["types"]],
                "stats": {s["stat"]["name"]: s["base_stat"] for s in d["stats"]}
            }

        data1 = load(p1)
        data2 = load(p2)

        return render_template("compare.html", p1=data1, p2=data2)

    return render_template("compare.html", p1=None, p2=None)


if __name__ == "__main__":
    init_db()
    #app.run(debug=True)
    app.run(host="0.0.0.0",port=5000)