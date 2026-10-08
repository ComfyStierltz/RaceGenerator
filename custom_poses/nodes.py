import json, os
import torch
from aiohttp import web
try:
    from server import PromptServer
except Exception:
    PromptServer = None
PACK_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
POSE_FILE = os.path.join(PACK_DIR, "custom_poses", "poses.json")

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
    names = ["none"]
    if os.path.isdir(folder):
        names += sorted(name for name in os.listdir(folder) if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")))
    return names

def chosen(store, selected):
    poses = store.get("poses") or []
    if selected == "all":
        return poses
    return [item for item in poses if item.get("name") == selected or selected.startswith((item.get("name") or "")[:2])]

def load_reference(name, width, height):
    import folder_paths
    from PIL import Image
    import numpy as np
    if not name or name == "none":
        return torch.zeros((1, height, width, 3)), True
    image = Image.open(os.path.join(folder_paths.get_input_directory(), name)).convert("RGB")
    arr = torch.from_numpy(np.array(image).astype("float32") / 255.0).unsqueeze(0)
    scaled = torch.nn.functional.interpolate(arr.permute(0, 3, 1, 2), size=(height, width), mode="area")
    return scaled.permute(0, 2, 3, 1), True

class SpriteCustomPoses:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "selected_pose": ("STRING", {"forceInput": True}),
            "loop_index": ("INT", {"default": 0, "min": 0, "max": 100, "forceInput": True}),
            "editing_pose": (pose_names(), {"default": pose_names()[0]}),
            "positive": ("STRING", {"multiline": True, "default": ""}),
            "pose_negative": ("STRING", {"multiline": True, "default": ""}),
            "width": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 16}),
            "height": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 16}),
            "denoise": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 1.0}),
            "reference_name": (input_files(), {"default": "none"}),
        }, "optional": {
            "gen_width": ("INT", {"default": 2080, "min": 512, "max": 4096, "step": 16, "forceInput": True}),
            "gen_height": ("INT", {"default": 3120, "min": 512, "max": 4096, "step": 16, "forceInput": True}),
        }}
    RETURN_TYPES = ("INT", "STRING", "STRING", "FLOAT", "IMAGE", "BOOLEAN")
    RETURN_NAMES = ("count", "positive", "negative", "denoise", "reference", "use_reference")
    FUNCTION = "run"
    CATEGORY = "sprite"

    def run(self, selected_pose, loop_index, editing_pose, positive, pose_negative, width, height, denoise, reference_name, gen_width=2080, gen_height=3120):
        store = load_store()
        poses = store.get("poses") or []
        for item in poses:
            if item.get("name") == editing_pose and positive.strip():
                item.update({"positive": positive, "negative": pose_negative, "width": width, "height": height, "denoise": denoise, "reference": reference_name})
        save_store(store)
        items = chosen(store, selected_pose)
        if not items:
            return (1, "", "", denoise, torch.zeros((1, 64, 64, 3)), False)
        item = items[min(loop_index, len(items) - 1)]
        scale = gen_width / 2080
        pose_width = int(round((int(item.get("width") or gen_width) * scale) / 16) * 16)
        pose_height = int(round((int(item.get("height") or gen_height) * scale) / 16) * 16)
        image, used = load_reference(item.get("reference"), pose_width, pose_height)
        print(f"[RaceGenerator] custom prompt {loop_index + 1}/{len(items)} {item.get('name')} reference={used}")
        return (len(items), item.get("positive") or "", item.get("negative") or "", float(item.get("denoise") or denoise), image, used)

if PromptServer is not None:
    @PromptServer.instance.routes.get("/sprite_preset/custom_poses")
    async def sprite_custom_poses(request):
        return web.json_response(load_store())
    @PromptServer.instance.routes.post("/sprite_preset/save_custom_pose")
    async def sprite_save_custom_pose(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name:
            return web.json_response({"error": "bad name"}, status=400)
        store = load_store()
        poses = store.setdefault("poses", [])
        payload = {"name": name, "positive": data.get("positive") or "", "negative": data.get("negative") or "", "width": int(data.get("width") or 0), "height": int(data.get("height") or 0), "denoise": float(data.get("denoise") or 0.8), "reference": data.get("reference") or "none"}
        item = next((pose for pose in poses if pose.get("name") == name), None)
        poses.append(payload) if item is None else item.update(payload)
        save_store(store)
        return web.json_response({"ok": True, "names": [pose["name"] for pose in poses]})

NODE_CLASS_MAPPINGS = {"SpriteCustomPoses": SpriteCustomPoses}
NODE_DISPLAY_NAME_MAPPINGS = {"SpriteCustomPoses": "Custom poses"}
