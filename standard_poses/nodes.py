import json, os
from aiohttp import web
try:
    from server import PromptServer
except Exception:
    PromptServer = None
PACK_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
POSE_FILE = os.path.join(PACK_DIR, "standard_poses", "poses.json")

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

def chosen(store, selected):
    poses = store.get("poses") or []
    if selected == "all":
        return poses
    return [item for item in poses if item.get("name") == selected or selected.startswith((item.get("name") or "")[:2])]

class SpriteStandardPoses:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "selected_pose": ("STRING", {"forceInput": True}),
            "loop_index": ("INT", {"default": 0, "min": 0, "max": 100, "forceInput": True}),
            "editing_pose": (pose_names(), {"default": pose_names()[0]}),
            "positive": ("STRING", {"multiline": True, "default": ""}),
            "pose_negative": ("STRING", {"multiline": True, "default": ""}),
            "shared_negative": ("STRING", {"multiline": True, "default": ""}),
        }}
    RETURN_TYPES = ("INT", "STRING", "STRING")
    RETURN_NAMES = ("count", "positive", "negative")
    FUNCTION = "run"
    CATEGORY = "sprite"

    def run(self, selected_pose, loop_index, editing_pose, positive, pose_negative, shared_negative):
        store = load_store()
        poses = store.get("poses") or []
        for item in poses:
            if item.get("name") == editing_pose and positive.strip():
                item["positive"] = positive
                item["negative"] = pose_negative
        store["negative"] = shared_negative
        save_store(store)
        items = chosen(store, selected_pose)
        if not items:
            return (1, "", shared_negative)
        item = items[min(loop_index, len(items) - 1)]
        negative = ", ".join(part for part in (shared_negative, item.get("negative") or "") if part and part.strip())
        print(f"[RaceGenerator] standard prompt {loop_index + 1}/{len(items)} {item.get('name')}")
        return (len(items), item.get("positive") or "", negative)

if PromptServer is not None:
    @PromptServer.instance.routes.get("/sprite_preset/standard_poses")
    async def sprite_standard_poses(request):
        return web.json_response(load_store())
    @PromptServer.instance.routes.post("/sprite_preset/save_standard_pose")
    async def sprite_save_standard_pose(request):
        data = await request.json()
        name = (data.get("name") or "").strip()
        if not name:
            return web.json_response({"error": "bad name"}, status=400)
        store = load_store()
        poses = store.setdefault("poses", [])
        item = next((pose for pose in poses if pose.get("name") == name), None)
        payload = {"name": name, "positive": data.get("positive") or "", "negative": data.get("negative") or ""}
        poses.append(payload) if item is None else item.update(payload)
        if "shared_negative" in data:
            store["negative"] = data.get("shared_negative") or ""
        save_store(store)
        return web.json_response({"ok": True, "names": [pose["name"] for pose in poses]})

NODE_CLASS_MAPPINGS = {"SpriteStandardPoses": SpriteStandardPoses}
NODE_DISPLAY_NAME_MAPPINGS = {"SpriteStandardPoses": "Standard poses"}
