import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "stierltz.tabs",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "StierltzRaceClothes") return;

        const TAB_H = 28;
        const origOnDrawForeground = nodeType.prototype.onDrawForeground;
        const origOnMouseDown = nodeType.prototype.onMouseDown;
        const origComputeSize = nodeType.prototype.computeSize;

        nodeType.prototype.onNodeCreated = function () {
            this._tab = "race";
            this._tabs = [
                { id: "race", label: "Race" },
                { id: "clothes", label: "Clothes" }
            ];
        };

        nodeType.prototype.computeSize = function (out) {
            const size = origComputeSize?.apply(this, arguments) || [340, 200];
            size[1] += TAB_H;
            return size;
        };

        nodeType.prototype.onDrawForeground = function (ctx) {
            origOnDrawForeground?.apply(this, arguments);
            if (!this._tabs) return;

            const tabW = this.size[0] / this._tabs.length;
            ctx.save();
            ctx.font = "13px Arial";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            this._tabs.forEach((tab, i) => {
                const x = i * tabW;
                const active = this._tab === tab.id;
                ctx.fillStyle = active ? "#444" : "#2a2a2a";
                ctx.fillRect(x, 0, tabW, TAB_H);
                ctx.strokeStyle = "#666";
                ctx.strokeRect(x, 0, tabW, TAB_H);
                ctx.fillStyle = active ? "#fff" : "#aaa";
                ctx.fillText(tab.label, x + tabW / 2, TAB_H / 2);
            });
            ctx.restore();
        };

        nodeType.prototype.onMouseDown = function (e, local_pos, graphCanvas) {
            if (local_pos[1] < TAB_H && this._tabs) {
                const tabW = this.size[0] / this._tabs.length;
                const idx = Math.floor(local_pos[0] / tabW);
                if (this._tabs[idx]) {
                    this._tab = this._tabs[idx].id;
                    this._applyTabVisibility();
                    this.setDirtyCanvas(true);
                    return true;
                }
            }
            return origOnMouseDown?.apply(this, arguments);
        };

        nodeType.prototype._applyTabVisibility = function () {
            const raceOnly = ["race", "gender_male", "race_positive", "race_negative"];
            const clothesOnly = ["clothes", "clothes_positive"];
            for (const w of this.widgets || []) {
                if (raceOnly.includes(w.name)) w.hidden = this._tab !== "race";
                if (clothesOnly.includes(w.name)) w.hidden = this._tab !== "clothes";
            }
            this.setSize(this.computeSize());
        };
    }
});
