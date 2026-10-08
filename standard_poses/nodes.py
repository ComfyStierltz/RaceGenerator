import json, os
PACK = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.realpath(__file__)))
POSE_FILE = os.path.join(PACK, "standard_poses", "poses.json")
SLOTS = 7

def load_store():
    if not os.path.isfile(POSE_FILE):
        return {"negative": "", "poses": []}
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
        }}
    RETURN_TYPES = tuple(["STRING"] * (2 + SLOTS))
    RETURN_NAMES = tuple(["pose_names", "shared_negative"] + [f"pose_{i:02d}_positive" for i in range(1, SLOTS + 1)])
    FUNCTION = "run"
    CATEGORY = "sprite"
    def run(self, editing_pose, positive, pose_negative, shared_negative):
        store = load_store()
        poses = store.get("poses") or []
        for item in poses:
            if item.get("name") == editing_pose and positive.strip():
                item["positive"] = positive
                item["negative"] = pose_negative
        store["negative"] = shared_negative
        save_store(store)
        texts = []
        for i in range(SLOTS):
            item = poses[i] if i < len(poses) else {}
            extra = ", ".join(part for part in (shared_negative, item.get("negative") or "") if part and part.strip())
            texts.append(item.get("positive") or "")
        names = "\n".join(item.get("name") or "" for item in poses)
        return tuple([names, shared_negative] + texts)

NODE_CLASS_MAPPINGS = {"SpriteStandardPoses": SpriteStandardPoses}
NODE_DISPLAY_NAME_MAPPINGS = {"SpriteStandardPoses": "Standard poses"}
