import json, os
import torch
PACK = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def load(folder):
    path = os.path.join(PACK, folder, "poses.json")
    if not os.path.isfile(path):
        return {"negative": "", "poses": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def plate(name, width, height):
    import folder_paths
    from PIL import Image
    import numpy as np
    if not name or name in ("none", ""):
        return torch.zeros((1, max(height, 64), max(width, 64), 3)), True
    image = Image.open(os.path.join(folder_paths.get_input_directory(), name)).convert("RGB")
    arr = torch.from_numpy(np.array(image).astype("float32") / 255.0).unsqueeze(0)
    scaled = torch.nn.functional.interpolate(arr.permute(0, 3, 1, 2), size=(height, width), mode="area")
    return scaled.permute(0, 2, 3, 1), True

class SpritePoseStep:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "selected_pose": ("STRING", {"forceInput": True}),
            "loop_index": ("INT", {"default": 0, "min": 0, "max": 100, "forceInput": True}),
            "gen_width": ("INT", {"default": 2080, "min": 512, "max": 4096, "forceInput": True}),
            "gen_height": ("INT", {"default": 3120, "min": 512, "max": 4096, "forceInput": True}),
        }}
    RETURN_TYPES = ("STRING", "STRING", "FLOAT", "IMAGE", "BOOLEAN", "INT", "INT")
    RETURN_NAMES = ("positive", "negative", "denoise", "reference", "use_reference", "save_width", "save_height")
    FUNCTION = "run"
    CATEGORY = "sprite"
    def run(self, selected_pose, loop_index, gen_width, gen_height):
        standard = load("standard_poses")
        custom = load("custom_poses")
        standard_items = standard.get("poses") or []
        custom_items = custom.get("poses") or []
        if selected_pose == "all":
            names = standard_items + custom_items
            item = names[min(loop_index, len(names) - 1)] if names else {}
            is_custom = loop_index >= len(standard_items)
        else:
            item = next((row for row in standard_items + custom_items if row.get("name") == selected_pose or selected_pose.startswith((row.get("name") or "")[:2])), {})
            is_custom = item in custom_items
        if not is_custom:
            positive = ", ".join(part for part in (standard.get("shared_positive") or "", item.get("positive") or "") if part and part.strip())
            negative = ", ".join(part for part in (standard.get("negative") or "", item.get("negative") or "") if part and part.strip())
            denoise = 0.5 if loop_index == 0 and selected_pose in ("all", "01 front") else 0.82
            print(f"[RaceGenerator] step {loop_index} standard {item.get('name')} denoise={denoise}")
            return (positive, negative, denoise, torch.zeros((1, 64, 64, 3)), False, gen_width, gen_height)
        scale = gen_width / 2080
        width = int(round((int(item.get("width") or gen_width) * scale) / 16) * 16)
        height = int(round((int(item.get("height") or gen_height) * scale) / 16) * 16)
        image, used = plate(item.get("reference"), width, height)
        print(f"[RaceGenerator] step {loop_index} custom {item.get('name')} {width}x{height}")
        return (item.get("positive") or "", item.get("negative") or "", float(item.get("denoise") or 0.9), image, used, width, height)

NODE_CLASS_MAPPINGS = {"SpritePoseStep": SpritePoseStep}
NODE_DISPLAY_NAME_MAPPINGS = {"SpritePoseStep": "Pose step"}


class SpriteResolution:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"high_res": ("BOOLEAN", {"default": True})}}
    RETURN_TYPES = ("INT", "INT", "INT", "INT")
    RETURN_NAMES = ("gen_width", "gen_height", "save_width", "save_height")
    FUNCTION = "run"
    CATEGORY = "sprite"
    def run(self, high_res):
        if high_res:
            print("[RaceGenerator] resolution 2080x3120, save 1040x1560")
            return (2080, 3120, 1040, 1560)
        print("[RaceGenerator] resolution 1040x1560")
        return (1040, 1560, 1040, 1560)

NODE_CLASS_MAPPINGS["SpriteResolution"] = SpriteResolution
NODE_DISPLAY_NAME_MAPPINGS["SpriteResolution"] = "Resolution"
