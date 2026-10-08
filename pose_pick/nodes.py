POSES = ["all", "01 front", "02 three-quarter left", "03 profile left", "04 three-quarter back left", "05 back", "06 profile right", "07 three-quarter right", "08 squat", "09 rear"]


class SpritePosePick:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pose": (POSES, {"default": "all"}),
                "standard_poses": ("STRING", {"forceInput": True}),
                "custom_poses": ("STRING", {"forceInput": True}),
                "loop_index": ("INT", {"default": 0, "min": 0, "max": 100, "forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING", "INT", "BOOLEAN")
    RETURN_NAMES = ("selected_pose", "count", "custom_turn")
    FUNCTION = "run"
    CATEGORY = "sprite"

    def check_lazy_status(self, **kwargs):
        return []

    def run(self, pose, standard_poses, custom_poses, loop_index):
        standard = [name for name in standard_poses.splitlines() if name.strip()]
        custom = [name for name in custom_poses.splitlines() if name.strip()]
        if pose == "all":
            names = standard + custom
            current = names[min(loop_index, len(names) - 1)] if names else "01 front"
            custom_turn = current in custom
        else:
            names = [pose]
            current = pose
            custom_turn = pose in custom or pose.startswith("08") or pose.startswith("09")
        print(f"[RaceGenerator] pose {loop_index + 1}/{max(len(names), 1)} {current} custom={custom_turn}")
        return (current, max(len(names), 1), custom_turn)


NODE_CLASS_MAPPINGS = {"SpritePosePick": SpritePosePick}
NODE_DISPLAY_NAME_MAPPINGS = {"SpritePosePick": "Pose pick"}
