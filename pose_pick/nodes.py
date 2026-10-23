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
            "all_poses": ("BOOLEAN", {"default": True}),
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
    def run(self, all_poses, pose, standard_poses, custom_poses):
        standard = [name for name in standard_poses.splitlines() if name.strip()]
        custom = [name for name in custom_poses.splitlines() if name.strip()]
        use_all = bool(all_poses) or pose == "all"
        file_count = len(file_names("standard_poses")) + len(file_names("custom_poses"))
        count = max(file_count, len(standard) + len(custom), 1) if use_all else 1
        selected = "all" if use_all else pose
        print(f"[RaceGenerator] pick all={use_all} pose={selected} count={count}")
        return (selected, count)

NODE_CLASS_MAPPINGS = {"SpritePosePick": SpritePosePick}
NODE_DISPLAY_NAME_MAPPINGS = {"SpritePosePick": "Pose pick"}
