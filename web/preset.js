import { app } from "../../scripts/app.js";

function widget(node, name) {
    return node.widgets?.find((item) => item.name === name);
}

function setCombo(node, name, values, selected) {
    const item = widget(node, name);
    if (!item) return;
    item.options = item.options || {};
    item.options.values = values;
    if (selected) item.value = selected;
}

app.registerExtension({
    name: "RaceGenerator.presets",
    async nodeCreated(node) {
        if (node.comfyClass !== "SpritePromptPreset") return;
        const race = widget(node, "race_preset");
        const clothes = widget(node, "clothes_preset");
        if (race) {
            const previous = race.callback;
            race.callback = async function () {
                const response = await fetch("/sprite_preset/race?name=" + encodeURIComponent(this.value));
                if (response.ok) {
                    const data = await response.json();
                    if (widget(node, "anatomy") && data.anatomy != null) widget(node, "anatomy").value = data.anatomy;
                    if (widget(node, "negative") && data.negative != null) widget(node, "negative").value = data.negative;
                    if (widget(node, "race_reference") && data.reference) widget(node, "race_reference").value = data.reference;
                }
                if (previous) return previous.apply(this, arguments);
            };
        }
        if (clothes) {
            const previous = clothes.callback;
            clothes.callback = async function () {
                const response = await fetch("/sprite_preset/clothes?name=" + encodeURIComponent(this.value));
                if (response.ok) {
                    const data = await response.json();
                    if (widget(node, "clothes") && data.clothes != null) widget(node, "clothes").value = data.clothes;
                }
                if (previous) return previous.apply(this, arguments);
            };
        }
        node.addWidget("button", "Загрузить референс", null, () => {
            const input = document.createElement("input");
            input.type = "file";
            input.accept = "image/*";
            input.onchange = async () => {
                const file = input.files && input.files[0];
                if (!file) return;
                const body = new FormData();
                body.append("image", file, file.name);
                const response = await fetch("/sprite_preset/upload_race", {method: "POST", body});
                const data = await response.json();
                if (!response.ok || !data.name) {
                    alert(data.error || "upload failed");
                    return;
                }
                setCombo(node, "race_reference", data.references || [data.name], data.name);
            };
            input.click();
        });
        node.addWidget("button", "Создать расу", null, async () => {
            const name = prompt("Имя новой расы");
            if (!name) return;
            const response = await fetch("/sprite_preset/save_body", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    name,
                    anatomy: widget(node, "anatomy")?.value || "",
                    negative: widget(node, "negative")?.value || "",
                    reference: widget(node, "race_reference")?.value || "none",
                }),
            });
            const data = await response.json();
            setCombo(node, "race_preset", data.names || [], name);
        });
        node.addWidget("button", "Создать одежду", null, async () => {
            const name = prompt("Имя новой одежды");
            if (!name) return;
            const response = await fetch("/sprite_preset/save_clothes", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({name, clothes: widget(node, "clothes")?.value || ""}),
            });
            const data = await response.json();
            setCombo(node, "clothes_preset", data.names || [], name);
        });
        node.setSize([Math.max(node.size[0], 620), node.size[1] + 100]);
    },
});
