import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "stierltz.tabs",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "StierltzRaceClothes") return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = origOnNodeCreated?.apply(this, arguments);

            // Tab state
            this._tab = "race";

            // Add tab switcher buttons at the top
            const raceBtn = this.addWidget("button", "► Race", null, () => this.switchTab("race"), { serialize: false });
            const clothesBtn = this.addWidget("button", "Clothes", null, () => this.switchTab("clothes"), { serialize: false });

            this.switchTab = (tab) => {
                this._tab = tab;
                raceBtn.name = tab === "race" ? "► Race" : "Race";
                clothesBtn.name = tab === "clothes" ? "► Clothes" : "Clothes";

                // Widget visibility by name
                const raceOnly = ["race", "gender_male", "race_positive", "race_negative"];
                const clothesOnly = ["clothes", "clothes_positive"];

                for (const w of this.widgets || []) {
                    if (raceOnly.includes(w.name)) w.hidden = tab !== "race";
                    if (clothesOnly.includes(w.name)) w.hidden = tab !== "clothes";
                }
                this.setSize(this.computeSize());
                this.setDirtyCanvas(true);
            };

            // Initial
            setTimeout(() => this.switchTab("race"), 100);
            return r;
        };
    }
});
