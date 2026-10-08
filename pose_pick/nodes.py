import json, os
PACK = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def file_names(folder):
    path = os.path.join(PACK, folder, "poses.json")
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        store = json.load(f)
    return [item.get("name") for item in store.get("poses", []) if item.get("name")]

def pose_choices():
    return ["all"] + file_names("standard_poses") + file_names("custom_poses")

class SpritePosePick:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "pose": (pose_choices(), {"default": "all"}),
            "standard_poses": ("STRING", {"forceInput": True}),
            "custom_poses": ("STRING", {"forceInput": True}),
        }}
    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("selected_pose", "count")
    FUNCTION = "run"
    CATEGORY = "sprite"
    def check_lazy_status(self, **kwargs):
        return []
    def run(self, pose, standard_poses, custom_poses):
        standard = [name for name in standard_poses.splitlines() if name.strip()]
        custom = [name for name in custom_poses.splitlines() if name.strip()]
        count = max(len(standard) + len(custom), 1) if pose == "all" else 1
        print(f"[RaceGenerator] pick {pose} count={count} custom={custom}")
        return (pose, count)

NODE_CLASS_MAPPINGS = {"SpritePosePick": SpritePosePick}
NODE_DISPLAY_NAME_MAPPINGS = {"SpritePosePick": "Pose pick"}
