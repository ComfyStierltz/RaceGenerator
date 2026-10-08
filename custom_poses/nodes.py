import json, os
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
    names = ["none"]
    if os.path.isdir(folder):
        names += sorted(name for name in os.listdir(folder) if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")))
    return names

class SpriteCustomPoses:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "editing_pose": (pose_names(), {"default": pose_names()[0]}),
            "positive": ("STRING", {"multiline": True, "default": ""}),
            "pose_negative": ("STRING", {"multiline": True, "default": ""}),
            "width": ("INT", {"default": 2496, "min": 512, "max": 4096, "step": 16}),
            "height": ("INT", {"default": 2080, "min": 512, "max": 4096, "step": 16}),
            "denoise": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01}),
            "reference": (input_files(), {"default": "none", "image_upload": True}),
        }}
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("pose_names",)
    FUNCTION = "run"
    OUTPUT_NODE = True
    CATEGORY = "sprite"
    def run(self, editing_pose, positive, pose_negative, width, height, denoise, reference):
        store = load_store()
        poses = store.get("poses") or []
        for item in poses:
            if item.get("name") == editing_pose and positive.strip():
                item.update({
                    "positive": positive,
                    "negative": pose_negative,
                    "width": int(width),
                    "height": int(height),
                    "denoise": float(denoise),
                    "reference": reference or "none",
                })
        save_store(store)
        current = next((item for item in poses if item.get("name") == editing_pose), {})
        shown = current.get("reference") or reference or "none"
        images = []
        if shown not in ("none", ""):
            images = [{"filename": shown, "subfolder": "", "type": "input"}]
        return {"ui": {"images": images}, "result": ("\n".join(item.get("name") or "" for item in poses),)}

NODE_CLASS_MAPPINGS = {"SpriteCustomPoses": SpriteCustomPoses}
NODE_DISPLAY_NAME_MAPPINGS = {"SpriteCustomPoses": "Custom poses"}
