import json, os
PACK = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
POSE_FILE = os.path.join(PACK, "standard_poses", "poses.json")
SLOTS = 7

def load_store():
    if not os.path.isfile(POSE_FILE):
        return {"shared_positive": "", "negative": "", "poses": []}
    with open(POSE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_store(store):
    os.makedirs(os.path.dirname(POSE_FILE), exist_ok=True)
    with open(POSE_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)

def pose_names():
    names = [item.get("name") for item in load_store().get("poses", []) if item.get("name")]
    return names or ["01 front"]

class SpriteStandardPoses:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "editing_pose": (pose_names(), {"default": pose_names()[0]}),
            "positive": ("STRING", {"multiline": True, "default": ""}),
            "pose_negative": ("STRING", {"multiline": True, "default": ""}),
            "shared_negative": ("STRING", {"multiline": True, "default": ""}),
            "shared_positive": ("STRING", {"multiline": True, "default": ""}),
        }}
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("pose_names",)
    FUNCTION = "run"
    CATEGORY = "sprite"
    def run(self, editing_pose, positive, pose_negative, shared_negative, shared_positive):
        store = load_store()
        poses = store.get("poses") or []
        for item in poses:
            if item.get("name") == editing_pose and positive.strip():
                item["positive"] = positive
                item["negative"] = pose_negative
        if shared_negative.strip():
            store["negative"] = shared_negative
        if shared_positive.strip():
            store["shared_positive"] = shared_positive
        save_store(store)
        return ("\n".join(item.get("name") or "" for item in poses),)

NODE_CLASS_MAPPINGS = {"SpriteStandardPoses": SpriteStandardPoses}
NODE_DISPLAY_NAME_MAPPINGS = {"SpriteStandardPoses": "Standard poses"}
