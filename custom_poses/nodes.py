import json, os
import torch
from aiohttp import web
try:
    from server import PromptServer
except Exception:
    PromptServer = None
PACK = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
POSE_FILE = os.path.join(PACK, "custom_poses", "poses.json")

def load_store():
    if not os.path.isfile(POSE_FILE):
        return {"poses": []}
    with open(POSE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_store(store):
    os.makedirs(os.path.dirname(POSE_FILE), exist_ok=True)
    with open(POSE_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)

def pose_names():
    names = [item.get("name") for item in load_store().get("poses", []) if item.get("name")]
    return names or ["08 squat"]

def input_files():
    import folder_paths
    folder = folder_paths.get_input_directory()
    names = ["none", ""]
    if os.path.isdir(folder):
        names += sorted(name for name in os.listdir(folder) if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")))
    return names

def load_reference(name, width, height):
    import folder_paths
    from PIL import Image
    import numpy as np
    if not name or name in ("none", ""):
        return torch.zeros((1, height, width, 3)), True
    image = Image.open(os.path.join(folder_paths.get_input_directory(), name)).convert("RGB")
    arr = torch.from_numpy(np.array(image).astype("float32") / 255.0).unsqueeze(0)
    scaled = torch.nn.functional.interpolate(arr.permute(0, 3, 1, 2), size=(height, width), mode="area")
    return scaled.permute(0, 2, 3, 1), True

class SpriteCustomPoses:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "editing_pose": (pose_names(), {"default": pose_names()[0]}),
            "positive": ("STRING", {"multiline": True, "default": ""}),
            "pose_negative": ("STRING", {"multiline": True, "default": ""}),
            "width": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 16}),
            "height": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 16}),
            "denoise": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 1.0}),
            "reference_name": (input_files(), {"default": "none"}),
        }}
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("pose_names",)
    FUNCTION = "run"
    CATEGORY = "sprite"
    def run(self, editing_pose, positive, pose_negative, width, height, denoise, reference_name):
        store = load_store()
        poses = store.get("poses") or []
        for item in poses:
            if item.get("name") == editing_pose and positive.strip():
                item.update({"positive": positive, "negative": pose_negative, "width": width, "height": height, "denoise": denoise, "reference": reference_name or "none"})
        save_store(store)
        return ("\n".join(item.get("name") or "" for item in poses),)

class SpriteCustomPrompt:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "selected_pose": ("STRING", {"forceInput": True}),
            "loop_index": ("INT", {"default": 0, "min": 0, "max": 100, "forceInput": True}),
        }, "optional": {
            "gen_width": ("INT", {"default": 2080, "min": 512, "max": 4096, "step": 16, "forceInput": True}),
            "gen_height": ("INT", {"default": 3120, "min": 512, "max": 4096, "step": 16, "forceInput": True}),
        }}
    RETURN_TYPES = ("STRING", "STRING", "FLOAT", "IMAGE", "BOOLEAN", "BOOLEAN")
    RETURN_NAMES = ("positive", "negative", "denoise", "reference", "use_reference", "active")
    FUNCTION = "run"
    CATEGORY = "sprite"
    def run(self, selected_pose, loop_index, gen_width=2080, gen_height=3120):
        store = load_store()
        poses = store.get("poses") or []
        if selected_pose == "all":
            items = poses
            item = items[min(max(loop_index - 7, 0), len(items) - 1)] if items else {}
        else:
            items = [item for item in poses if item.get("name") == selected_pose or selected_pose.startswith((item.get("name") or "")[:2])]
            item = items[0] if items else {}
        if not item:
            return ("", "", 0.8, torch.zeros((1, 64, 64, 3)), False, False)
        scale = gen_width / 2080
        pose_width = int(round((int(item.get("width") or gen_width) * scale) / 16) * 16)
        pose_height = int(round((int(item.get("height") or gen_height) * scale) / 16) * 16)
        image, used = load_reference(item.get("reference"), pose_width, pose_height)
        print(f"[RaceGenerator] custom {item.get('name')} reference={used}")
        active = (selected_pose == "all" and loop_index >= 7) or selected_pose.startswith(("08", "09"))
        return (item.get("positive") or "", item.get("negative") or "", float(item.get("denoise") or 0.8), image, used, active)

NODE_CLASS_MAPPINGS = {"SpriteCustomPoses": SpriteCustomPoses, "SpriteCustomPrompt": SpriteCustomPrompt}
NODE_DISPLAY_NAME_MAPPINGS = {"SpriteCustomPoses": "Custom poses", "SpriteCustomPrompt": "Custom pose prompt"}
