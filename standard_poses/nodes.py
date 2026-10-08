import json, os
from aiohttp import web
try:
    from server import PromptServer
except Exception:
    PromptServer = None
PACK = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
POSE_FILE = os.path.join(PACK, "standard_poses", "poses.json")

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
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("pose_names",)
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
        return ("\n".join(item.get("name") or "" for item in poses),)

class SpriteStandardPrompt:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "selected_pose": ("STRING", {"forceInput": True}),
            "loop_index": ("INT", {"default": 0, "min": 0, "max": 100, "forceInput": True}),
        }}
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "run"
    CATEGORY = "sprite"
    def run(self, selected_pose, loop_index):
        store = load_store()
        poses = store.get("poses") or []
        if selected_pose == "all":
            items = poses
        else:
            items = [item for item in poses if item.get("name") == selected_pose or selected_pose.startswith((item.get("name") or "")[:2])]
        if not items:
            return ("", store.get("negative") or "")
        item = items[min(loop_index, len(items) - 1)]
        negative = ", ".join(part for part in (store.get("negative") or "", item.get("negative") or "") if part and part.strip())
        print(f"[RaceGenerator] standard {item.get('name')}")
        return (item.get("positive") or "", negative)

if PromptServer is not None:
    @PromptServer.instance.routes.get("/sprite_preset/standard_poses")
    async def sprite_standard_poses(request):
        return web.json_response(load_store())

NODE_CLASS_MAPPINGS = {"SpriteStandardPoses": SpriteStandardPoses, "SpriteStandardPrompt": SpriteStandardPrompt}
NODE_DISPLAY_NAME_MAPPINGS = {"SpriteStandardPoses": "Standard poses", "SpriteStandardPrompt": "Standard pose prompt"}
