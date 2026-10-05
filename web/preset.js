import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

function widget(node, name) {
  return node.widgets?.find((w) => w.name === name);
}

function moveBefore(node, item, beforeName) {
  const list = node.widgets;
  const from = list.indexOf(item);
  const to = list.findIndex((w) => w.name === beforeName);
  if (from < 0 || to < 0 || from === to) return;
  list.splice(from, 1);
  list.splice(to, 0, item);
}

async function store() {
  const res = await api.fetchApi("/sprite_preset/list");
  return await res.json();
}

function fillCombo(w, names, selected) {
  if (!w) return;
  w.options.values = names.length ? names : ["(пусто)"];
  if (selected && w.options.values.includes(selected)) w.value = selected;
  else if (!w.options.values.includes(w.value)) w.value = w.options.values[0];
}

app.registerExtension({
  name: "sprite.promptpreset",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name === "SpriteStandardPoses") {
      const origPose = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function () {
        const r = origPose?.apply(this, arguments);
        const node = this;
        const add = node.addWidget("button", "add pose", null, async () => {
          const name = prompt("Pose name", "");
          if (!name || !name.trim()) return;
          await api.fetchApi("/sprite_preset/save_pose", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              name: name.trim(),
              positive: widget(node, "positive")?.value || "",
              negative: widget(node, "negative")?.value || "",
              denoise: widget(node, "denoise")?.value || 0.6,
            }),
          });
          const data = await (await api.fetchApi("/sprite_preset/poses")).json();
          fillCombo(widget(node, "pose"), (data.poses || []).map((p) => p.name), name.trim());
        });
        add.serialize = false;
        moveBefore(node, add, "pose");
        const poseWidget = widget(node, "pose");
        const loadSelected = async () => {
          const data = await (await api.fetchApi("/sprite_preset/poses")).json();
          const item = (data.poses || []).find((p) => p.name === poseWidget.value);
          if (!item) return;
          widget(node, "positive").value = item.positive || "";
          widget(node, "negative").value = item.negative || "";
          widget(node, "denoise").value = item.denoise || 0.6;
        };
        if (poseWidget) {
          const old = poseWidget.callback;
          poseWidget.callback = function () { old?.apply(this, arguments); loadSelected(); };
        }
        api.fetchApi("/sprite_preset/poses").then((res) => res.json()).then((data) => {
          fillCombo(widget(node, "pose"), (data.poses || []).map((p) => p.name), poseWidget?.value);
        });
        return r;
      };
      return;
    }
    if (nodeData.name === "SpriteCustomPoses") {
      const origCustom = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function () {
        const r = origCustom?.apply(this, arguments);
        const node = this;
        const add = node.addWidget("button", "add pose", null, async () => {
          const name = prompt("Pose name", "");
          if (!name || !name.trim()) return;
          await api.fetchApi("/sprite_preset/save_custom_pose", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              name: name.trim(),
              positive: widget(node, "positive")?.value || "",
              negative: widget(node, "negative")?.value || "",
              denoise: widget(node, "denoise")?.value || 0.86,
              use_reference: widget(node, "use_reference")?.value || false,
              width: widget(node, "width")?.value || 1560,
              height: widget(node, "height")?.value || 1560,
            }),
          });
          const data = await (await api.fetchApi("/sprite_preset/custom_poses")).json();
          fillCombo(widget(node, "pose"), (data.poses || []).map((p) => p.name), name.trim());
        });
        add.serialize = false;
        moveBefore(node, add, "pose");
        const poseWidget = widget(node, "pose");
        const loadSelected = async () => {
          const data = await (await api.fetchApi("/sprite_preset/custom_poses")).json();
          const item = (data.poses || []).find((p) => p.name === poseWidget.value);
          if (!item) return;
          widget(node, "positive").value = item.positive || "";
          widget(node, "negative").value = item.negative || "";
          widget(node, "denoise").value = item.denoise || 0.86;
          widget(node, "use_reference").value = !!item.use_reference;
          widget(node, "width").value = item.width || 1560;
          widget(node, "height").value = item.height || 1560;
        };
        if (poseWidget) {
          const old = poseWidget.callback;
          poseWidget.callback = function () { old?.apply(this, arguments); loadSelected(); };
        }
        return r;
      };
      return;
    }
    if (nodeData.name === "SpritePresetSelect") {
      const orig = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function () {
        const r = orig?.apply(this, arguments);
        const node = this;
        store().then((data) => {
          fillCombo(widget(node, "race_preset"), data.races || [], widget(node, "race_preset")?.value);
          fillCombo(widget(node, "clothes_preset"), data.clothes || ["naked"], widget(node, "clothes_preset")?.value);
        });
        return r;
      };
      return;
    }
    if (nodeData.name !== "SpritePromptPreset") return;
    const orig = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = orig?.apply(this, arguments);
      const node = this;
      const saveRace = node.addWidget("button", "создать пресет расы", null, async () => {
        const name = prompt("Имя файла расы", widget(node, "race_preset")?.value || "");
        if (!name || !name.trim()) return;
        await api.fetchApi("/sprite_preset/save_body", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name.trim(),
            anatomy: widget(node, "anatomy")?.value || "",
            negative: widget(node, "negative")?.value || "",
          }),
        });
        fillCombo(widget(node, "race_preset"), (await store()).races || [], name.trim());
      });
      saveRace.serialize = false;
      const saveClothes = node.addWidget("button", "создать пресет одежды", null, async () => {
        const name = prompt("Имя файла одежды", widget(node, "clothes_preset")?.value || "");
        if (!name || !name.trim() || name.trim() === "naked") return;
        await api.fetchApi("/sprite_preset/save_clothes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: name.trim(), clothes: widget(node, "clothes")?.value || "" }),
        });
        fillCombo(widget(node, "clothes_preset"), (await store()).clothes || [], name.trim());
      });
      saveClothes.serialize = false;
      moveBefore(node, saveRace, "race_preset");
      moveBefore(node, saveClothes, "clothes_preset");
      store().then((data) => {
        fillCombo(widget(node, "race_preset"), data.races || [], widget(node, "race_preset")?.value);
        fillCombo(widget(node, "clothes_preset"), data.clothes || [], widget(node, "clothes_preset")?.value);
      });
      return r;
    };
  },
});
