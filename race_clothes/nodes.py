import json
import os
import re

from aiohttp import web

try:
    from server import PromptServer
except Exception:
    PromptServer = None

PACK_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
RACE_DIR = os.path.join(PACK_DIR, "races")
CLOTHES_DIR = os.path.join(PACK_DIR, "clothes")
NAKED = "naked"


def slug(name):
    clean = re.sub(r"[^0-9A-Za-zА-Яа-я_\- ]+", "", name).strip().replace(" ", "_")
    return clean or "preset"


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def race_files():
    os.makedirs(RACE_DIR, exist_ok=True)
    return sorted(p for p in os.listdir(RACE_DIR) if p.endswith(".json"))


def clothes_files():
    os.makedirs(CLOTHES_DIR, exist_ok=True)
    return sorted(p for p in os.listdir(CLOTHES_DIR) if p.endswith(".json"))


def race_names():
    found = []
    for name in race_files():
        data = read_json(os.path.join(RACE_DIR, name))
        found.append(data.get("name") or name[:-5])
    return found or ["(пусто)"]


def clothes_names():
    found = [NAKED]
    for name in clothes_files():
        data = read_json(os.path.join(CLOTHES_DIR, name))
        found.append(data.get("name") or name[:-5])
    return found


def race_folder():
    import folder_paths
    folder = os.path.join(folder_paths.get_input_directory(), "RaceGenerator", "races")
    os.makedirs(folder, exist_ok=True)
    return folder


def race_images():
    names = ["none"]
    for name in sorted(os.listdir(race_folder())):
        if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")):
            names.append(f"RaceGenerator/races/{name}")
    return names


def load_race(name):
    for file_name in race_files():
        data = read_json(os.path.join(RACE_DIR, file_name))
        if data.get("name") == name or file_name[:-5] == name:
            return data
    return {}


def load_clothes(name):
    if not name or name == NAKED:
        return ""
    for file_name in clothes_files():
        data = read_json(os.path.join(CLOTHES_DIR, file_name))
        if data.get("name") == name or file_name[:-5] == name:
            return data.get("text") or ""
    return ""


def save_race(name, anatomy, negative, reference="none", gender="female"):
    os.makedirs(RACE_DIR, exist_ok=True)
    path = os.path.join(RACE_DIR, slug(name) + ".json")
    current = {}
    if os.path.isfile(path):
        current = read_json(path)
    if "genders" not in current:
        current["genders"] = {}
    current["name"] = name
    current["genders"][gender] = {"anatomy": anatomy, "negative": negative}
    current["reference"] = reference
    with open(path, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)


def save_clothes(name, text):
    if name == NAKED:
        return
    os.makedirs(CLOTHES_DIR, exist_ok=True)
    path = os.path.join(CLOTHES_DIR, slug(name) + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"name": name, "text": text}, f, ensure_ascii=False, indent=2)


class StierltzRaceClothes:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "race": (race_names(), {"default": race_names()[0]}),
                "clothes": (clothes_names(), {"default": NAKED}),
                "gender_male": ("BOOLEAN", {"default": False}),
                "race_positive": ("STRING", {"multiline": True, "default": ""}),
                "race_negative": ("STRING", {"multiline": True, "default": ""}),
                "clothes_positive": ("STRING", {"multiline": True, "default": ""}),
                "clothes_negative": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "run"
    CATEGORY = "sprite"

    def run(self, race, clothes, gender_male, race_positive, race_negative, clothes_positive, clothes_negative):
        gender = "male" if gender_male else "female"
        if race and race != "(пусто)":
            save_race(race, race_positive, race_negative, "none", gender)
        if clothes and clothes != NAKED and clothes_positive.strip():
            save_clothes(clothes, clothes_positive)
        positive = race_positive
        negative = race_negative
        if clothes != NAKED and clothes_positive.strip():
            positive = f"{positive}, {clothes_positive}" if positive else clothes_positive
        if clothes_negative.strip():
            negative = f"{negative}, {clothes_negative}" if negative else clothes_negative
        return (positive, negative)


if PromptServer is not None:
    @PromptServer.instance.routes.get("/stierltz/list")
    async def stierltz_list(request):
        return web.json_response({"races": race_names(), "clothes": clothes_names()})

    @PromptServer.instance.routes.get("/stierltz/race")
    async def stierltz_race(request):
        name = request.query.get("name", "")
        gender = request.query.get("gender", "female")
        data = load_race(name)
        genders = data.get("genders", {})
        if gender in genders:
            return web.json_response(genders[gender])
        return web.json_response({"anatomy": data.get("anatomy", ""), "negative": data.get("negative", "")})

    @PromptServer.instance.routes.get("/stierltz/clothes")
    async def stierltz_clothes(request):
        name = request.query.get("name", "")
        return web.json_response({"text": load_clothes(name)})

    @PromptServer.instance.routes.post("/stierltz/save_race")
    async def stierltz_save_race(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        gender = data.get("gender", "female")
        if not name:
            return web.json_response({"error": "empty name"}, status=400)
        save_race(name, data.get("anatomy") or "", data.get("negative") or "", "none", gender)
        return web.json_response({"ok": True, "names": race_names()})

    @PromptServer.instance.routes.post("/stierltz/save_clothes")
    async def stierltz_save_clothes(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name or name == NAKED:
            return web.json_response({"error": "bad name"}, status=400)
        save_clothes(name, data.get("text") or "")
        return web.json_response({"ok": True, "names": clothes_names()})


NODE_CLASS_MAPPINGS = {
    "StierltzRaceClothes": StierltzRaceClothes,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "StierltzRaceClothes": "Race & Clothes",
}
