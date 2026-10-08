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
    names = ["all"] + file_names("standard_poses") + file_names("custom_poses")
    return names or ["all", "01 front", "08 squat", "09 rear"]

class SpritePosePick:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "pose": (pose_choices(), {"default": "all"}),
            "standard_poses": ("STRING", {"forceInput": True}),
            "custom_poses": ("STRING", {"forceInput": True}),
            "high_res": ("BOOLEAN", {"default": True}),
            "clothes_on": ("BOOLEAN", {"default": True}),
        }}
    RETURN_TYPES = ("STRING", "INT", "INT", "INT", "INT", "INT", "BOOLEAN")
    RETURN_NAMES = ("selected_pose", "count", "gen_width", "gen_height", "save_width", "save_height", "clothes_on")
    FUNCTION = "run"
    CATEGORY = "sprite"
    def check_lazy_status(self, **kwargs):
        return []
    def run(self, pose, standard_poses, custom_poses, high_res, clothes_on):
        standard = [name for name in standard_poses.splitlines() if name.strip()]
        custom = [name for name in custom_poses.splitlines() if name.strip()]
        count = max(len(standard) + len(custom), 1) if pose == "all" else 1
        if high_res:
            gen_w, gen_h, save_w, save_h = 2080, 3120, 1040, 1560
        else:
            gen_w, gen_h, save_w, save_h = 1040, 1560, 1040, 1560
        print(f"[RaceGenerator] pick {pose} count={count} high_res={high_res} clothes={clothes_on} custom={custom}")
        return (pose, count, gen_w, gen_h, save_w, save_h, bool(clothes_on))

NODE_CLASS_MAPPINGS = {"SpritePosePick": SpritePosePick}
NODE_DISPLAY_NAME_MAPPINGS = {"SpritePosePick": "Pose pick"}
