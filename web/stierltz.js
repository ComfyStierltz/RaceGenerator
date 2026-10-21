import { app } from "../../../scripts/app.js";

const TAB_H = 38;
const TOP_MARGIN = 8; // gap above tabs

app.registerExtension({
    name: "stierltz.RaceClothesTabs",

    async nodeCreated(node) {
        if (node.comfyClass !== "StierltzRaceClothes") return;

        node._tab = "race";
        node._tabs = [
            { id: "race", label: "Race" },
            { id: "clothes", label: "Clothes" }
        ];

        // Invisible spacer that reserves space for the tab bar
        const spacer = node.addWidget("button", "", "", () => {}, { serialize: false });
        spacer.computeSize = () => [node.size[0], TOP_MARGIN + TAB_H + 6];
        spacer.hidden = false;
        // Move to front of widget list
        const si = node.widgets.indexOf(spacer);
        if (si > 0) {
            node.widgets.splice(si, 1);
            node.widgets.unshift(spacer);
        }

        const origDraw = node.onDrawForeground;
        node.onDrawForeground = function (ctx) {
            // Draw tabs in the spacer area
            if (this._tabs) {
                const w = this.size[0];
                const tabW = w / this._tabs.length;
                const y = TOP_MARGIN;
                ctx.save();
                ctx.font = "bold 14px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                this._tabs.forEach((tab, i) => {
                    const x = i * tabW;
                    const active = this._tab === tab.id;
                    ctx.fillStyle = active ? "#5a3d8a" : "#333";
                    ctx.fillRect(x + 2, y, tabW - 4, TAB_H);
                    ctx.strokeStyle = active ? "#c4b5fd" : "#666";
                    ctx.lineWidth = active ? 2 : 1;
                    ctx.strokeRect(x + 2.5, y + 0.5, tabW - 5, TAB_H - 1);
                    ctx.fillStyle = active ? "#fff" : "#bbb";
                    ctx.fillText(tab.label, x + tabW / 2, y + TAB_H / 2);
                });
                ctx.restore();
            }
            if (origDraw) origDraw.apply(this, arguments);
        };

        const origMouse = node.onMouseDown;
        node.onMouseDown = function (e, localPos) {
            if (localPos && localPos[1] >= TOP_MARGIN && localPos[1] < TOP_MARGIN + TAB_H && this._tabs) {
                const tabW = this.size[0] / this._tabs.length;
                const idx = Math.floor(localPos[0] / tabW);
                if (this._tabs[idx]) {
                    this._tab = this._tabs[idx].id;
                    this._applyVisibility();
                    this.setDirtyCanvas(true, true);
                    return true;
                }
            }
            return origMouse ? origMouse.apply(this, arguments) : false;
        };

        node._applyVisibility = function () {
            const raceOnly = ["race", "gender_male", "race_positive", "race_negative"];
            const clothesOnly = ["clothes", "clothes_positive"];
            for (const w of this.widgets || []) {
                if (w === spacer) continue;
                if (raceOnly.includes(w.name)) w.hidden = this._tab !== "race";
                if (clothesOnly.includes(w.name)) w.hidden = this._tab !== "clothes";
            }
            this.setSize(this.computeSize());
        };

        setTimeout(() => node._applyVisibility?.(), 120);
    }
});
