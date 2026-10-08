import json, os
PACK = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def load(name):
    path = os.path.join(PACK, name)
    if not os.path.isfile(path):
        return {"poses": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def pick(store, selected):
    poses = store.get("poses") or []
    if selected == "all":
        return poses
    return [item for item in poses if item.get("name") == selected or selected.startswith((item.get("name") or "")[:2])]

class SpritePoseCount:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"selected_pose": ("STRING", {"forceInput": True})}}
    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("standard_count", "custom_count")
    FUNCTION = "run"
    CATEGORY = "sprite"

    def run(self, selected_pose):
        standard = len(pick(load("standard_poses/poses.json"), selected_pose))
        custom = len(pick(load("custom_poses/poses.json"), selected_pose))
        print(f"[RaceGenerator] cycle standard={standard} custom={custom} for {selected_pose}")
        return (max(standard, 1), max(custom, 1))

NODE_CLASS_MAPPINGS = {"SpritePoseCount": SpritePoseCount}
NODE_DISPLAY_NAME_MAPPINGS = {"SpritePoseCount": "Pose cycle count"}
