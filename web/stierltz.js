import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "stierltz.RaceClothesTabs",

    async nodeCreated(node) {
        if (node.comfyClass !== "StierltzRaceClothes") return;

        node._tab = "race";

        // Tab buttons as real widgets (they participate in layout)
        const raceBtn = node.addWidget("button", "Race", null, () => {
            node._tab = "race";
            node._applyVisibility();
            node.setDirtyCanvas(true);
        }, { serialize: false });

        const clothesBtn = node.addWidget("button", "Clothes", null, () => {
            node._tab = "clothes";
            node._applyVisibility();
            node.setDirtyCanvas(true);
        }, { serialize: false });

        // Move tab buttons to the top of the widget list
        const moveToFront = (w) => {
            const i = node.widgets.indexOf(w);
            if (i > 0) {
                node.widgets.splice(i, 1);
                node.widgets.unshift(w);
            }
        };
        moveToFront(clothesBtn);
        moveToFront(raceBtn);

        node._applyVisibility = function () {
            const raceOnly = ["race", "gender_male", "race_positive", "race_negative"];
            const clothesOnly = ["clothes", "clothes_positive"];
            for (const w of this.widgets || []) {
                if (w === raceBtn || w === clothesBtn) continue;
                if (raceOnly.includes(w.name)) w.hidden = this._tab !== "race";
                if (clothesOnly.includes(w.name)) w.hidden = this._tab !== "clothes";
            }
            // Visual feedback on buttons
            raceBtn.name = this._tab === "race" ? "► Race" : "Race";
            clothesBtn.name = this._tab === "clothes" ? "► Clothes" : "Clothes";
            this.setSize(this.computeSize());
        };

        setTimeout(() => node._applyVisibility?.(), 100);
    }
});
