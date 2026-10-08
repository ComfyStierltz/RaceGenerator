import json
import os

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


class SpriteStandardPoses:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "selected_pose": ("STRING", {"forceInput": True}),
                "editing_pose": (pose_names(), {"default": pose_names()[0]}),
                "positive": ("STRING", {"multiline": True, "default": ""}),
                "pose_negative": ("STRING", {"multiline": True, "default": ""}),
                "shared_negative": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "run"
    CATEGORY = "sprite"

    def run(self, selected_pose, editing_pose, positive, pose_negative, shared_negative):
        store = load_store()
        poses = store.get("poses") or []
        for item in poses:
            if item.get("name") == editing_pose and positive.strip():
                item["positive"] = positive
                item["negative"] = pose_negative
        store["negative"] = shared_negative
        save_store(store)
        chosen = next((item for item in poses if item.get("name") == selected_pose or selected_pose.startswith((item.get("name") or "")[:2])), None)
        if selected_pose == "all" or chosen is None:
            chosen = next((item for item in poses if item.get("name") == editing_pose), poses[0] if poses else {})
        pose_positive = (chosen or {}).get("positive") or positive
        pose_negative = ", ".join(part for part in (shared_negative, (chosen or {}).get("negative") or "") if part and part.strip())
        print(f"[RaceGenerator] standard prompt {chosen.get('name') if chosen else editing_pose}")
        return (pose_positive, pose_negative)


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
        if item is None:
            poses.append(payload)
        else:
            item.update(payload)
        if "shared_negative" in data:
            store["negative"] = data.get("shared_negative") or ""
        save_store(store)
        return web.json_response({"ok": True, "names": [pose["name"] for pose in poses]})


NODE_CLASS_MAPPINGS = {"SpriteStandardPoses": SpriteStandardPoses}
NODE_DISPLAY_NAME_MAPPINGS = {"SpriteStandardPoses": "Standard poses"}
