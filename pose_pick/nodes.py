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
        optional = {f"pose_{i:02d}": ("IMAGE", {"lazy": True}) for i in range(1, 10)}
        return {"required": {
            "pose": (pose_choices(), {"default": "all"}),
            "standard_poses": ("STRING", {"forceInput": True}),
            "custom_poses": ("STRING", {"forceInput": True}),
            "high_res": ("BOOLEAN", {"default": True}),
            "clothes_on": ("BOOLEAN", {"default": True}),
        }, "optional": optional}
    RETURN_TYPES = ("IMAGE", "INT", "INT", "INT", "INT", "BOOLEAN")
    RETURN_NAMES = ("images", "gen_width", "gen_height", "save_width", "save_height", "clothes_on")
    FUNCTION = "run"
    CATEGORY = "sprite"
    OUTPUT_NODE = True
    def check_lazy_status(self, pose, standard_poses="", custom_poses="", high_res=True, clothes_on=True, **images):
        wanted = [f"pose_{i:02d}" for i in range(1, 10)] if pose == "all" else [f"pose_{pose[:2]}"]
        missing = [key for key in wanted if images.get(key) is None]
        if missing:
            print(f"[RaceGenerator] pose pick requests {missing}")
        return missing
    def run(self, pose, standard_poses="", custom_poses="", high_res=True, clothes_on=True, **images):
        import folder_paths, torch
        from pathlib import Path
        from PIL import Image
        if high_res:
            gen_w, gen_h, save_w, save_h = 2080, 3120, 1040, 1560
        else:
            gen_w, gen_h, save_w, save_h = 1040, 1560, 1040, 1560
        wanted = [f"pose_{i:02d}" for i in range(1, 10)] if pose == "all" else [f"pose_{pose[:2]}"]
        frames = [images[key][0] for key in wanted if images.get(key) is not None]
        print(f"[RaceGenerator] pose pick kept {len(frames)} for {pose}")
        if not frames:
            return (torch.zeros((1, 64, 64, 4)), gen_w, gen_h, save_w, save_h, bool(clothes_on))
        return (torch.stack([frame.cpu() for frame in frames], 0) if all(frame.shape == frames[0].shape for frame in frames) else frames[0].unsqueeze(0), gen_w, gen_h, save_w, save_h, bool(clothes_on))

NODE_CLASS_MAPPINGS = {"SpritePosePick": SpritePosePick}
NODE_DISPLAY_NAME_MAPPINGS = {"SpritePosePick": "Pose pick"}
