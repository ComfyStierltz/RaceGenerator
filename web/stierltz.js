import { app } from "../../../scripts/app.js";

const TAB_H = 40;

app.registerExtension({
    name: "stierltz.RaceClothesTabs",

    async nodeCreated(node) {
        if (node.comfyClass !== "StierltzRaceClothes") return;

        node._tab = "race";
        node._tabs = [
            { id: "race", label: "Race" },
            { id: "clothes", label: "Clothes" }
        ];

        // Spacer widget at the top to push content down
        const spacer = node.addWidget("button", "", "", () => {}, { serialize: false });
        spacer.computeSize = () => [0, TAB_H];
        spacer.hidden = false;
        // Move spacer to front
        const idx = node.widgets.indexOf(spacer);
        if (idx > 0) {
            node.widgets.splice(idx, 1);
            node.widgets.unshift(spacer);
        }

        const origComputeSize = node.computeSize;
        node.computeSize = function () {
            const size = origComputeSize ? origComputeSize.apply(this, arguments) : [340, 240];
            return size;
        };

        const origDraw = node.onDrawForeground;
        node.onDrawForeground = function (ctx) {
            // Draw tab bar at the very top
            if (this._tabs) {
                const w = this.size[0];
                const tabW = w / this._tabs.length;
                ctx.save();
                ctx.font = "bold 14px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                this._tabs.forEach((tab, i) => {
                    const x = i * tabW;
                    const active = this._tab === tab.id;
                    ctx.fillStyle = active ? "#5a3d8a" : "#2a2a2a";
                    ctx.fillRect(x, 0, tabW, TAB_H);
                    ctx.strokeStyle = active ? "#c4b5fd" : "#555";
                    ctx.lineWidth = active ? 2 : 1;
                    ctx.strokeRect(x + 0.5, 0.5, tabW - 1, TAB_H - 1);
                    ctx.fillStyle = active ? "#fff" : "#aaa";
                    ctx.fillText(tab.label, x + tabW / 2, TAB_H / 2);
                });
                ctx.restore();
            }
            if (origDraw) origDraw.apply(this, arguments);
        };

        const origMouse = node.onMouseDown;
        node.onMouseDown = function (e, localPos) {
            if (localPos && localPos[1] < TAB_H && this._tabs) {
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

        setTimeout(() => node._applyVisibility?.(), 150);
    }
});
