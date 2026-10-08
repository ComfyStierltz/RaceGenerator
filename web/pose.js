import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "RaceGenerator.customPose",
    async nodeCreated(node) {
        if (node.comfyClass !== "SpriteCustomPoses") return;
        const pose = node.widgets?.find((w) => w.name === "editing_pose");
        if (!pose) return;
        const previous = pose.callback;
        pose.callback = async function () {
            const response = await fetch("/racegenerator/custom_pose?name=" + encodeURIComponent(this.value));
            if (response.ok) {
                const item = await response.json();
                for (const widget of node.widgets) {
                    if (widget.name === "positive" && item.positive != null) widget.value = item.positive;
                    if (widget.name === "pose_negative" && item.negative != null) widget.value = item.negative;
                    if (widget.name === "width" && item.width) widget.value = item.width;
                    if (widget.name === "height" && item.height) widget.value = item.height;
                    if (widget.name === "denoise" && item.denoise != null) widget.value = item.denoise;
                    if (widget.name === "reference" && item.reference) widget.value = item.reference;
                    if (widget.name === "use_reference") widget.value = !!item.use_reference;
                }
            }
            if (previous) return previous.apply(this, arguments);
        };
    },
});
