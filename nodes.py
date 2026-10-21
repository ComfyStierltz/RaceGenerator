import json
from pathlib import Path
from aiohttp import web
import folder_paths
from server import PromptServer

class StierltzRaceClothes:
    @classmethod
    def INPUT_TYPES(cls):
        races = cls._list_races()
        clothes = cls._list_clothes()
        return {
            "required": {
                "race": (["none"] + races, {"default": "none"}),
                "clothes": (["none"] + clothes, {"default": "none"}),
                "gender_male": ("BOOLEAN", {"default": False, "label_on": "male", "label_off": "female"}),
            },
            "optional": {
                "race_positive": ("STRING", {"multiline": True, "default": ""}),
                "race_negative": ("STRING", {"multiline": True, "default": ""}),
                "clothes_positive": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "build"
    CATEGORY = "stierltz"

    @staticmethod
    def _base_dir():
        base = Path(folder_paths.get_input_directory()) / "stierltz"
        base.mkdir(parents=True, exist_ok=True)
        return base

    @classmethod
    def _races_dir(cls):
        d = cls._base_dir() / "races"
        d.mkdir(exist_ok=True)
        return d

    @classmethod
    def _clothes_dir(cls):
        d = cls._base_dir() / "clothes"
        d.mkdir(exist_ok=True)
        return d

    @classmethod
    def _list_races(cls):
        return sorted([f.stem for f in cls._races_dir().glob("*.json")])

    @classmethod
    def _list_clothes(cls):
        return sorted([f.stem for f in cls._clothes_dir().glob("*.json")])

    @classmethod
    def _load(cls, folder: Path, name: str):
        if not name or name == "none":
            return {}
        p = folder / f"{name}.json"
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    @classmethod
    def _save(cls, folder: Path, name: str, data: dict):
        if not name or name == "none":
            return
        p = folder / f"{name}.json"
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def build(self, race, clothes, gender_male, race_positive="", race_negative="", clothes_positive=""):
        races_dir = self._races_dir()
        clothes_dir = self._clothes_dir()

        race_data = self._load(races_dir, race)
        clothes_data = self._load(clothes_dir, clothes)

        if race != "none" and (race_positive or race_negative):
            changed = False
            if race_positive and race_positive != race_data.get("positive", ""):
                race_data["positive"] = race_positive
                changed = True
            if race_negative and race_negative != race_data.get("negative", ""):
                race_data["negative"] = race_negative
                changed = True
            if changed:
                self._save(races_dir, race, race_data)

        if clothes != "none" and clothes_positive:
            if clothes_positive != clothes_data.get("positive", ""):
                clothes_data["positive"] = clothes_positive
                self._save(clothes_dir, clothes, clothes_data)

        r_pos = race_data.get("positive") or race_positive or ""
        r_neg = race_data.get("negative") or race_negative or ""
        c_pos = clothes_data.get("positive") or clothes_positive or ""

        gender = "male" if gender_male else "female"
        parts = []
        if r_pos.strip():
            parts.append(r_pos.strip())
        if c_pos.strip() and clothes != "none":
            parts.append(c_pos.strip())
        else:
            parts.append("completely nude, no clothes, naked")

        positive = f"{gender}, " + ", ".join(parts) if parts else gender
        negative = r_neg.strip()
        return (positive, negative)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")


# API endpoints
@PromptServer.instance.routes.get("/stierltz/race/{name}")
async def get_race(request):
    name = request.match_info["name"]
    data = StierltzRaceClothes._load(StierltzRaceClothes._races_dir(), name)
    return web.json_response(data)

@PromptServer.instance.routes.get("/stierltz/clothes/{name}")
async def get_clothes(request):
    name = request.match_info["name"]
    data = StierltzRaceClothes._load(StierltzRaceClothes._clothes_dir(), name)
    return web.json_response(data)

@PromptServer.instance.routes.get("/stierltz/list")
async def list_all(request):
    return web.json_response({
        "races": StierltzRaceClothes._list_races(),
        "clothes": StierltzRaceClothes._list_clothes(),
    })


NODE_CLASS_MAPPINGS = {
    "StierltzRaceClothes": StierltzRaceClothes,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StierltzRaceClothes": "Stierltz Race & Clothes",
}
