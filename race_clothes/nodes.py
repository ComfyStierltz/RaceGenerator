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


def save_race(name, anatomy, negative, reference="none"):
    os.makedirs(RACE_DIR, exist_ok=True)
    path = os.path.join(RACE_DIR, slug(name) + ".json")
    current = {}
    if os.path.isfile(path):
        current = read_json(path)
    data = {
        "name": name,
        "anatomy": anatomy if anatomy else current.get("anatomy") or "",
        "negative": negative if negative else current.get("negative") or "",
        "reference": reference or current.get("reference") or "none",
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_clothes(name, text):
    if name == NAKED:
        return
    os.makedirs(CLOTHES_DIR, exist_ok=True)
    path = os.path.join(CLOTHES_DIR, slug(name) + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"name": name, "text": text}, f, ensure_ascii=False, indent=2)


class SpritePromptPreset:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "race_preset": (race_names(), {"default": race_names()[0]}),
                "anatomy": ("STRING", {"multiline": True, "default": ""}),
                "negative": ("STRING", {"multiline": True, "default": ""}),
                "clothes_preset": (clothes_names(), {"default": clothes_names()[0]}),
                "clothes": ("STRING", {"multiline": True, "default": ""}),
                "race_reference": (race_images(), {"default": "none", "image_upload": True}),
                "copy_face": ("BOOLEAN", {"default": True}),
                "copy_body": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "IMAGE")
    RETURN_NAMES = ("anatomy", "negative", "clothes", "reference")
    FUNCTION = "run"
    OUTPUT_NODE = True
    CATEGORY = "sprite"

    def run(self, race_preset, anatomy, negative, clothes_preset, clothes, race_reference="none", copy_face=True, copy_body=True):
        import folder_paths
        from PIL import Image
        import numpy as np
        import torch
        folder = os.path.join(folder_paths.get_input_directory(), "RaceGenerator", "races")
        os.makedirs(folder, exist_ok=True)
        if race_preset and race_preset != "(пусто)":
            save_race(race_preset, anatomy, negative, race_reference or "none")
        if clothes_preset and clothes_preset != NAKED and clothes.strip():
            save_clothes(clothes_preset, clothes)
        if clothes_preset == NAKED:
            clothes = ""
        shown = race_reference or "none"
        images = []
        if shown not in ("none", ""):
            path = shown if os.path.isabs(shown) else os.path.join(folder_paths.get_input_directory(), shown)
            if os.path.isfile(path):
                image = Image.open(path).convert("RGB")
                arr = torch.from_numpy(__import__("numpy").array(image).astype("float32") / 255.0).unsqueeze(0)
                images = [{"filename": os.path.basename(path), "subfolder": os.path.relpath(os.path.dirname(path), folder_paths.get_input_directory()), "type": "input"}]
                return {"ui": {"images": images}, "result": (anatomy, negative, clothes, arr)}
        blank = torch.zeros((1, 64, 64, 3))
        return {"ui": {"images": []}, "result": (anatomy, negative, clothes, blank)}



class SpritePresetSelect:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "apply": ("BOOLEAN", {"default": True}),
                "race_preset": (race_names(), {"default": race_names()[0]}),
                "clothes_preset": (clothes_names(), {"default": NAKED}),
            },
            "optional": {
                "anatomy_in": ("STRING", {"forceInput": True}),
                "negative_in": ("STRING", {"forceInput": True}),
                "clothes_in": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "BOOLEAN")
    RETURN_NAMES = ("anatomy", "negative", "clothes", "use_clothes")
    FUNCTION = "run"
    CATEGORY = "sprite"

    def run(self, apply, race_preset, clothes_preset, anatomy_in="", negative_in="", clothes_in=""):
        if not apply:
            text = clothes_in or ""
            return (anatomy_in or "", negative_in or "", text, bool(text.strip()))
        data = load_race(race_preset)
        clothes = load_clothes(clothes_preset)
        return (data.get("anatomy") or "", data.get("negative") or "", clothes, clothes_preset != NAKED and bool(clothes.strip()))


if PromptServer is not None:
    @PromptServer.instance.routes.get("/sprite_preset/list")
    async def sprite_preset_list(request):
        return web.json_response({"races": race_names(), "clothes": clothes_names(), "references": race_images()})

    @PromptServer.instance.routes.post("/sprite_preset/upload_race")
    async def sprite_preset_upload_race(request):
        reader = await request.multipart()
        field = await reader.next()
        if field is None:
            return web.json_response({"error": "no file"}, status=400)
        name = os.path.basename(field.filename or "race.png")
        folder = race_folder()
        path = os.path.join(folder, name)
        size = 0
        with open(path, "wb") as handle:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                size += len(chunk)
                handle.write(chunk)
        rel = f"RaceGenerator/races/{name}"
        return web.json_response({"ok": True, "name": rel, "references": race_images()})

    @PromptServer.instance.routes.post("/sprite_preset/save_body")
    async def sprite_preset_save_body(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name:
            return web.json_response({"error": "empty name"}, status=400)
        save_race(name, data.get("anatomy") or "", data.get("negative") or "", data.get("reference") or "none")
        return web.json_response({"ok": True, "names": race_names()})

    @PromptServer.instance.routes.get("/sprite_preset/race")
    async def sprite_preset_race(request):
        return web.json_response(load_race(request.query.get("name", "")))

    @PromptServer.instance.routes.get("/sprite_preset/clothes")
    async def sprite_preset_clothes(request):
        name = request.query.get("name", "")
        return web.json_response({"name": name, "clothes": load_clothes(name)})

    @PromptServer.instance.routes.post("/sprite_preset/save_clothes")
    async def sprite_preset_save_clothes(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name or name == NAKED:
            return web.json_response({"error": "bad name"}, status=400)
        save_clothes(name, data.get("clothes") or "")
        return web.json_response({"ok": True, "names": clothes_names()})

NODE_CLASS_MAPPINGS = {
    "SpritePromptPreset": SpritePromptPreset,
    "SpritePresetSelect": SpritePresetSelect,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "SpritePromptPreset": "Race and clothes presets",
    "SpritePresetSelect": "Race and clothes select",
}
