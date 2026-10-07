POSES = [
    "all",
    "01 front",
    "02 three-quarter left",
    "03 profile left",
    "04 three-quarter back left",
    "05 back",
    "06 profile right",
    "07 three-quarter right",
    "08 custom squat",
    "09 custom rear",
]
POSE_INPUT = {pose: f"pose_{i:02d}" for i, pose in enumerate(POSES) if i}


class SpritePosePick:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {f"pose_{i:02d}": ("IMAGE", {"lazy": True}) for i in range(1, 10)}
        return {
            "required": {
                "pose": (POSES, {"default": "01 front"}),
                "output_folder": ("STRING", {"default": "sprites"}),
            },
            "optional": optional,
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "selected_pose")
    FUNCTION = "run"
    CATEGORY = "sprite"
    OUTPUT_NODE = True

    def check_lazy_status(self, pose, output_folder, pose_01=None, pose_02=None, pose_03=None, pose_04=None, pose_05=None, pose_06=None, pose_07=None, pose_08=None, pose_09=None):
        have = {
            "pose_01": pose_01, "pose_02": pose_02, "pose_03": pose_03, "pose_04": pose_04,
            "pose_05": pose_05, "pose_06": pose_06, "pose_07": pose_07, "pose_08": pose_08, "pose_09": pose_09,
        }
        custom = {"08 custom squat": "pose_08", "09 custom rear": "pose_09"}
        if pose == "all":
            missing = [key for key in ("pose_08", "pose_09") if have.get(key) is None]
        elif pose in custom:
            key = custom[pose]
            missing = [key] if have.get(key) is None else []
        else:
            missing = []
        if missing:
            print(f"[RaceGenerator] pose pick requests only {missing}")
        return missing

    def run(self, pose, output_folder="sprites", pose_01=None, pose_02=None, pose_03=None, pose_04=None, pose_05=None, pose_06=None, pose_07=None, pose_08=None, pose_09=None):
        import folder_paths
        import torch
        from pathlib import Path
        from PIL import Image
        have = {
            "pose_01": pose_01, "pose_02": pose_02, "pose_03": pose_03, "pose_04": pose_04,
            "pose_05": pose_05, "pose_06": pose_06, "pose_07": pose_07, "pose_08": pose_08, "pose_09": pose_09,
        }
        names = {f"pose_{i:02d}": POSES[i] for i in range(1, 10)}
        wanted = list(have) if pose == "all" else [POSE_INPUT.get(pose, "pose_01")]
        out = Path(folder_paths.get_output_directory()) / (output_folder or "sprites")
        out.mkdir(parents=True, exist_ok=True)
        frames = []
        for key in wanted:
            image = have.get(key)
            if image is None:
                continue
            arr = (image[0].clamp(0, 1).cpu().numpy() * 255).astype("uint8")
            Image.fromarray(arr).save(out / f"{names[key].replace(' ', '_')}.png")
            frames.append(image[0])
        print(f"[RaceGenerator] pose pick saved {len(frames)} of requested {wanted}")
        if not frames:
            return (torch.zeros((1, 64, 64, 4)), pose)
        height = max(frame.shape[0] for frame in frames)
        width = max(frame.shape[1] for frame in frames)
        channels = max(frame.shape[2] for frame in frames)
        batch = []
        for frame in frames:
            canvas = torch.zeros((height, width, channels), dtype=frame.dtype, device=frame.device)
            canvas[:frame.shape[0], :frame.shape[1], :frame.shape[2]] = frame
            batch.append(canvas)
        return (torch.stack(batch, dim=0), pose)


NODE_CLASS_MAPPINGS = {"SpritePosePick": SpritePosePick}
NODE_DISPLAY_NAME_MAPPINGS = {"SpritePosePick": "Pose pick"}
