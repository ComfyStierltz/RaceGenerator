import json, os
import torch
PACK = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
POSE_FILE = os.path.join(PACK, "custom_poses", "poses.json")
SLOTS = 2

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
        return torch.zeros((1, max(height, 64), max(width, 64), 3)), True
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
        }, "optional": {
            "gen_width": ("INT", {"default": 2080, "min": 512, "max": 4096, "step": 16, "forceInput": True}),
            "gen_height": ("INT", {"default": 3120, "min": 512, "max": 4096, "step": 16, "forceInput": True}),
        }}
    RETURN_TYPES = tuple(["STRING"] + ["STRING", "STRING", "FLOAT", "IMAGE", "BOOLEAN"] * SLOTS)
    RETURN_NAMES = tuple(["pose_names"] + [name for i in range(1, SLOTS + 1) for name in (f"pose_{i:02d}_positive", f"pose_{i:02d}_negative", f"pose_{i:02d}_denoise", f"pose_{i:02d}_reference", f"pose_{i:02d}_use_reference")])
    FUNCTION = "run"
    CATEGORY = "sprite"
    def run(self, editing_pose, positive, pose_negative, width, height, denoise, reference_name, gen_width=2080, gen_height=3120):
        store = load_store()
        poses = store.get("poses") or []
        for item in poses:
            if item.get("name") == editing_pose and positive.strip():
                item.update({"positive": positive, "negative": pose_negative, "width": width, "height": height, "denoise": denoise, "reference": reference_name or "none"})
        save_store(store)
        scale = gen_width / 2080
        out = ["\n".join(item.get("name") or "" for item in poses)]
        for i in range(SLOTS):
            item = poses[i] if i < len(poses) else {}
            pose_width = int(round((int(item.get("width") or gen_width) * scale) / 16) * 16)
            pose_height = int(round((int(item.get("height") or gen_height) * scale) / 16) * 16)
            image, used = load_reference(item.get("reference"), pose_width, pose_height)
            out.extend([item.get("positive") or "", item.get("negative") or "", float(item.get("denoise") or denoise), image, used])
        return tuple(out)

NODE_CLASS_MAPPINGS = {"SpriteCustomPoses": SpriteCustomPoses}
NODE_DISPLAY_NAME_MAPPINGS = {"SpriteCustomPoses": "Custom poses"}
