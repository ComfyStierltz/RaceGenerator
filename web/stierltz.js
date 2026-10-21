import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "stierltz.tabs",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "StierltzRaceClothes") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated?.apply(this, arguments);

                // Create tab buttons
                this.addWidget("button", "Tab: Race", null, () => this.showTab("race"));
                this.addWidget("button", "Tab: Clothes", null, () => this.showTab("clothes"));

                this._currentTab = "race";
                this.showTab = (tab) => {
                    this._currentTab = tab;
                    // Hide/show widgets by name prefix or index
                    const raceWidgets = ["race", "gender_male", "race_positive", "race_negative"];
                    const clothesWidgets = ["clothes", "clothes_positive"];
                    this.widgets?.forEach(w => {
                        if (raceWidgets.includes(w.name)) {
                            w.hidden = tab !== "race";
                        }
                        if (clothesWidgets.includes(w.name)) {
                            w.hidden = tab !== "clothes";
                        }
                    });
                    this.setDirtyCanvas(true);
                };

                // Initial state
                setTimeout(() => this.showTab("race"), 50);
                return r;
            };
        }
    }
});
