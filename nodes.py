import json
import os
from pathlib import Path
import folder_paths

class StierltzRaceClothes:
    """
    Race & Clothes preset node.
    - Races stored in input/stierltz/races/<name>.json
    - Clothes stored in input/stierltz/clothes/<name>.json
    - Output: combined positive / negative prompts
    """

    @classmethod
    def INPUT_TYPES(cls):
        races = cls._list_races()
        clothes = cls._list_clothes()
        if "elf" not in races:
            races = ["elf"] + races
        if "dwarf" not in races:
            races = ["dwarf"] + races
        return {
            "required": {
                "race": (["none"] + races, {"default": "none"}),
                "clothes": (["none"] + clothes, {"default": "none"}),
                "gender_male": ("BOOLEAN", {"default": False, "label_on": "male", "label_off": "female"}),
            },
            "optional": {
                "race_positive": ("STRING", {"multiline": True, "default": "", "label": "Race Positive"}),
                "race_negative": ("STRING", {"multiline": True, "default": "", "label": "Race Negative"}),
                "clothes_positive": ("STRING", {"multiline": True, "default": "", "label": "Clothes Positive"}),
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
        d = cls._races_dir()
        return sorted([f.stem for f in d.glob("*.json")])

    @classmethod
    def _list_clothes(cls):
        d = cls._clothes_dir()
        return sorted([f.stem for f in d.glob("*.json")])

    @classmethod
    def _load_json(cls, folder: Path, name: str):
        if not name or name == "none":
            return {}
        p = folder / f"{name}.json"
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def build(self, race, clothes, gender_male, race_positive="", race_negative="", clothes_positive=""):
        races_dir = self._races_dir()
        clothes_dir = self._clothes_dir()

        race_data = self._load_json(races_dir, race)
        clothes_data = self._load_json(clothes_dir, clothes)

        # Prefer file data, fall back to widget values (for live editing)
        r_pos = race_data.get("positive") or race_positive or ""
        r_neg = race_data.get("negative") or race_negative or ""
        c_pos = clothes_data.get("positive") or clothes_positive or ""

        gender = "male" if gender_male else "female"

        # Build positive
        parts = []
        if r_pos.strip():
            parts.append(r_pos.strip())
        if c_pos.strip() and clothes != "none":
            parts.append(c_pos.strip())
        else:
            parts.append("completely nude, no clothes, naked")

        positive = ", ".join(parts)
        if gender:
            positive = f"{gender}, {positive}"

        # Negative
        negative = r_neg.strip() if r_neg.strip() else ""

        return (positive, negative)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")


class StierltzSaveRace:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": "new_race"}),
                "positive": ("STRING", {"multiline": True, "default": ""}),
                "negative": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "save"
    CATEGORY = "stierltz"
    OUTPUT_NODE = True

    def save(self, name, positive, negative):
        if not name or name.strip() == "":
            return ("error: empty name",)
        name = name.strip().replace(" ", "_")
        d = StierltzRaceClothes._races_dir()
        p = d / f"{name}.json"
        data = {"positive": positive, "negative": negative}
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return (f"saved race: {name}",)


class StierltzSaveClothes:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": "new_clothes"}),
                "positive": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "save"
    CATEGORY = "stierltz"
    OUTPUT_NODE = True

    def save(self, name, positive):
        if not name or name.strip() == "":
            return ("error: empty name",)
        name = name.strip().replace(" ", "_")
        d = StierltzRaceClothes._clothes_dir()
        p = d / f"{name}.json"
        data = {"positive": positive}
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return (f"saved clothes: {name}",)


NODE_CLASS_MAPPINGS = {
    "StierltzRaceClothes": StierltzRaceClothes,
    "StierltzSaveRace": StierltzSaveRace,
    "StierltzSaveClothes": StierltzSaveClothes,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StierltzRaceClothes": "Stierltz Race & Clothes",
    "StierltzSaveRace": "Stierltz Save Race",
    "StierltzSaveClothes": "Stierltz Save Clothes",
}
