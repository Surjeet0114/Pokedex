import requests
import csv
import webbrowser
from colorama import Fore, Style, init
init(autoreset=True)

base_url = "https://pokeapi.co/api/v2/pokemon"

def get_json(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    else:
        print("Failed:", r.status_code)
        return None

def save_search(name, poke_id, types):
    with open("history.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([name, poke_id, ",".join(types)])

def get_evolution_names(chain_data):
    names = []
    def traverse(node):
        names.append(node['species']['name'])
        for evo in node['evolves_to']:
            traverse(evo)
    traverse(chain_data['chain'])
    return names

def get_ability_effect(url):
    data = get_json(url)
    if not data:
        return None
    for entry in data.get('effect_entries', []):
        if entry['language']['name'] == 'en':
            return entry['short_effect']
    return None

def get_move_details(url):
    data = get_json(url)
    if not data:
        return None
    return {
        'name': data['name'],
        'power': data['power'],
        'pp': data['pp'],
        'accuracy': data['accuracy'],
        'type': data['type']['name'],
        'class': data['damage_class']['name']
    }

name = input("Enter Pokémon name: ").lower()
data = get_json(f"{base_url}/{name}")

if data:
    print(Fore.CYAN + "BASIC INFO")
    print("Name              :", Fore.YELLOW + data["name"].capitalize())
    print("ID                :", data["id"])
    print("Height            :", data["height"])
    print("Weight            :", data["weight"])
    print("Base Experience   :", data["base_experience"])

    types = [t["type"]["name"] for t in data["types"]]
    print("Types             :", Fore.GREEN + ", ".join(types))

    save_search(data["name"], data["id"], types)

    print(Fore.CYAN + "STATS")
    for s in data["stats"]:
        print(f"{s['stat']['name'].capitalize():15}: {s['base_stat']}")

    print(Fore.CYAN + "IMAGE LINKS")
    front = data["sprites"]["front_default"]
    back = data["sprites"]["back_default"]
    hd = data["sprites"]["other"]["official-artwork"]["front_default"]
    print("Front Sprite      :", front)
    print("Back Sprite       :", back)
    print("Official Artwork  :", hd)

    if hd:
        print(Fore.MAGENTA + "Opening Pokémon artwork...")
        webbrowser.open(hd)

    species = get_json(data["species"]["url"])
    if species:
        color = species["color"]["name"]
        habitat = species["habitat"]["name"] if species["habitat"] else "None"
        print(Fore.CYAN + "SPECIES INFO")
        print("Color             :", color)
        print("Habitat           :", habitat)

        flavor = None
        for entry in species["flavor_text_entries"]:
            if entry["language"]["name"] == "en":
                flavor = entry["flavor_text"].replace("\n", " ").replace("\f", " ")
                break
        if flavor:
            print("Flavor Text       :", Fore.YELLOW + flavor)

        evo_url = species.get("evolution_chain", {}).get("url")
        if evo_url:
            evo_data = get_json(evo_url)
            if evo_data:
                evo_names = get_evolution_names(evo_data)
                print(Fore.CYAN + "Evolution Chain   :", Fore.GREEN + " -> ".join(evo_names))

    print(Fore.CYAN + "ABILITY DETAILS")
    for a in data["abilities"]:
        ability_name = a["ability"]["name"]
        ability_url = a["ability"]["url"]
        effect = get_ability_effect(ability_url)
        label = ability_name + (" (hidden)" if a["is_hidden"] else "")
        print(Fore.YELLOW + f"- {label}: " + (effect or "No effect text found"))

    print(Fore.CYAN + "MOVE DETAILS")
    for m in data["moves"][:5]:
        move_info = get_move_details(m["move"]["url"])
        if move_info:
            print(Fore.GREEN + f"- {move_info['name']}")
            print(f"  Type      : {move_info['type']}")
            print(f"  Class     : {move_info['class']}")
            print(f"  Power     : {move_info['power']}")
            print(f"  PP        : {move_info['pp']}")
            print(f"  Accuracy  : {move_info['accuracy']}")
