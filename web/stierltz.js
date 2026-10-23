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

async function saveRace(node) {
    const race = widget(node, "race")?.value;
    if (!race || race === "(пусто)") return;
    const gender = widget(node, "gender_male")?.value ? "male" : "female";
    await fetch("/stierltz/save_race", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            name: race,
            gender,
            anatomy: widget(node, "race_positive")?.value || "",
            negative: widget(node, "race_negative")?.value || "",
        }),
    });
}

async function saveClothes(node) {
    const clothes = widget(node, "clothes")?.value;
    if (!clothes || clothes === "naked") return;
    await fetch("/stierltz/save_clothes", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            name: clothes,
            text: widget(node, "clothes_positive")?.value || "",
        }),
    });
}

async function loadRace(node) {
    const race = widget(node, "race")?.value;
    if (!race) return;
    const gender = widget(node, "gender_male")?.value ? "male" : "female";
    const response = await fetch(`/stierltz/race?name=${encodeURIComponent(race)}&gender=${gender}`);
    if (response.ok) {
        const data = await response.json();
        if (widget(node, "race_positive")) widget(node, "race_positive").value = data.anatomy || "";
        if (widget(node, "race_negative")) widget(node, "race_negative").value = data.negative || "";
    }
}

async function loadClothes(node) {
    const clothes = widget(node, "clothes")?.value;
    if (!clothes || clothes === "naked") {
        if (widget(node, "clothes_positive")) widget(node, "clothes_positive").value = "";
        return;
    }
    const response = await fetch(`/stierltz/clothes?name=${encodeURIComponent(clothes)}`);
    if (response.ok) {
        const data = await response.json();
        if (widget(node, "clothes_positive")) widget(node, "clothes_positive").value = data.text || "";
    }
}

app.registerExtension({
    name: "RaceGenerator.stierltz",
    async nodeCreated(node) {
        if (node.comfyClass !== "StierltzRaceClothes") return;

        const race = widget(node, "race");
        const clothes = widget(node, "clothes");
        const gender = widget(node, "gender_male");
        const racePos = widget(node, "race_positive");
        const raceNeg = widget(node, "race_negative");
        const clothesPos = widget(node, "clothes_positive");
        const clothesNeg = widget(node, "clothes_negative");

        if (race) {
            const prev = race.callback;
            race.callback = async function() {
                await loadRace(node);
                if (prev) return prev.apply(this, arguments);
            };
        }

        if (clothes) {
            const prev = clothes.callback;
            clothes.callback = async function() {
                await loadClothes(node);
                if (prev) return prev.apply(this, arguments);
            };
        }

        if (gender) {
            const prev = gender.callback;
            gender.callback = async function() {
                await saveRace(node);
                await loadRace(node);
                if (prev) return prev.apply(this, arguments);
            };
        }

        if (racePos) {
            const prev = racePos.callback;
            racePos.callback = async function() {
                await saveRace(node);
                if (prev) return prev.apply(this, arguments);
            };
        }

        if (raceNeg) {
            const prev = raceNeg.callback;
            raceNeg.callback = async function() {
                await saveRace(node);
                if (prev) return prev.apply(this, arguments);
            };
        }

        if (clothesPos) {
            const prev = clothesPos.callback;
            clothesPos.callback = async function() {
                await saveClothes(node);
                if (prev) return prev.apply(this, arguments);
            };
        }

        node.addWidget("button", "Создать расу", null, async () => {
            const name = prompt("Имя новой расы");
            if (!name) return;
            const response = await fetch("/stierltz/save_race", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    name,
                    gender: widget(node, "gender_male")?.value ? "male" : "female",
                    anatomy: widget(node, "race_positive")?.value || "",
                    negative: widget(node, "race_negative")?.value || "",
                }),
            });
            const data = await response.json();
            setCombo(node, "race", data.names || [], name);
        });

        node.addWidget("button", "Создать одежду", null, async () => {
            const name = prompt("Имя новой одежды");
            if (!name) return;
            const response = await fetch("/stierltz/save_clothes", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    name,
                    text: widget(node, "clothes_positive")?.value || "",
                }),
            });
            const data = await response.json();
            setCombo(node, "clothes", data.names || [], name);
        });

        node.setSize([Math.max(node.size[0], 400), node.size[1] + 80]);
    },
});
