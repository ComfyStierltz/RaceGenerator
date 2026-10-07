import json
import os
import re

from aiohttp import web

try:
    from server import PromptServer
except Exception:
    PromptServer = None

NODE_DIR = os.path.dirname(os.path.realpath(__file__))
RACE_DIR = os.path.join(NODE_DIR, "races")
CLOTHES_DIR = os.path.join(NODE_DIR, "clothes")
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


def load_race(name):
    for file_name in race_files():
        data = read_json(os.path.join(RACE_DIR, file_name))
        if data.get("name") == name or file_name[:-5] == name:
            return data.get("anatomy") or "", data.get("negative") or ""
    return "", ""


def load_clothes(name):
    if not name or name == NAKED:
        return ""
    for file_name in clothes_files():
        data = read_json(os.path.join(CLOTHES_DIR, file_name))
        if data.get("name") == name or file_name[:-5] == name:
            return data.get("text") or ""
    return ""


def save_race(name, anatomy, negative):
    os.makedirs(RACE_DIR, exist_ok=True)
    path = os.path.join(RACE_DIR, slug(name) + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"name": name, "anatomy": anatomy, "negative": negative}, f, ensure_ascii=False, indent=2)


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
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("anatomy", "negative", "clothes")
    FUNCTION = "run"
    CATEGORY = "sprite"

    def run(self, race_preset, anatomy, negative, clothes_preset, clothes):
        return (anatomy, negative, clothes)


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
        anatomy, negative = load_race(race_preset)
        clothes = load_clothes(clothes_preset)
        return (anatomy, negative, clothes, clothes_preset != NAKED and bool(clothes.strip()))


if PromptServer is not None:
    @PromptServer.instance.routes.get("/sprite_preset/list")
    async def sprite_preset_list(request):
        return web.json_response({"races": race_names(), "clothes": clothes_names()})

    @PromptServer.instance.routes.post("/sprite_preset/save_body")
    async def sprite_preset_save_body(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name:
            return web.json_response({"error": "empty name"}, status=400)
        save_race(name, data.get("anatomy") or "", data.get("negative") or "")
        return web.json_response({"ok": True, "names": race_names()})

    @PromptServer.instance.routes.post("/sprite_preset/save_clothes")
    async def sprite_preset_save_clothes(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name or name == NAKED:
            return web.json_response({"error": "bad name"}, status=400)
        save_clothes(name, data.get("clothes") or "")
        return web.json_response({"ok": True, "names": clothes_names()})


POSES = [
    "all",
    "01 front",
    "02 three-quarter left",
    "03 profile left",
    "04 three-quarter back left",
    "05 back",
    "06 profile right",
    "07 three-quarter right",
    "08 squat",
    "09 rear",
]


class SpritePosePick:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {f"pose_{i:02d}": ("IMAGE", {"lazy": True}) for i in range(1, 10)}
        return {"required": {"pose": (POSES, {"default": "all"}), "output_folder": ("STRING", {"default": "sprites"})}, "optional": optional}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "run"
    CATEGORY = "sprite"
    OUTPUT_NODE = True

    def check_lazy_status(self, pose, output_folder="sprites", **kwargs):
        needed = range(1, 10) if pose == "all" else [int(pose[:2])]
        missing = []
        for i in needed:
            key = f"pose_{i:02d}"
            if kwargs.get(key) is None:
                missing.append(key)
        return missing

    def run(self, pose, output_folder="sprites", **kwargs):
        import folder_paths
        from pathlib import Path
        from PIL import Image
        wanted = list(range(1, 10)) if pose == "all" else [int(pose[:2])]
        names = {i: POSES[i] for i in range(1, 10)}
        out = Path(folder_paths.get_output_directory()) / (output_folder or "sprites")
        out.mkdir(parents=True, exist_ok=True)
        shown = None
        for i in wanted:
            image = kwargs.get(f"pose_{i:02d}")
            if image is None:
                continue
            shown = image
            arr = (image[0].clamp(0, 1).cpu().numpy() * 255).astype("uint8")
            safe = names[i].replace(" ", "_")
            Image.fromarray(arr).save(out / f"{safe}.png")
        if shown is None:
            import torch
            shown = torch.zeros((1, 64, 64, 4))
        return (shown,)


NODE_CLASS_MAPPINGS = {
    "SpritePromptPreset": SpritePromptPreset,
    "SpritePresetSelect": SpritePresetSelect,
    "SpritePosePick": SpritePosePick,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "SpritePromptPreset": "Race and clothes presets",
    "SpritePresetSelect": "Race and clothes select",
    "SpritePosePick": "Pose pick",
}
