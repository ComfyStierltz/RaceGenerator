import { app } from "../../scripts/app.js";
app.registerExtension({
  name: "RaceGenerator.presets",
  async beforeRegisterNodeDef(nodeType) {
    const title = nodeType.comfyClass;
    if (title !== "SpriteStandardPoses" && title !== "SpriteCustomPoses") return;
    const orig = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const result = orig?.apply(this, arguments);
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "Add pose";
      button.style.width = "100%";
      this.addDOMWidget("add_pose", "button", button);
      return result;
    };
  },
});
