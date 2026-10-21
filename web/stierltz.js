import { app } from "../../scripts/app.js";

const TAB_H = 32;

app.registerExtension({
    name: "stierltz.RaceClothesTabs",

    async nodeCreated(node) {
        if (node.comfyClass !== "StierltzRaceClothes") return;

        node._tab = "race";
        node._tabs = [
            { id: "race", label: "Race" },
            { id: "clothes", label: "Clothes" }
        ];

        // Force redraw
        const origDraw = node.onDrawForeground;
        node.onDrawForeground = function (ctx) {
            if (origDraw) origDraw.apply(this, arguments);

            if (!this._tabs) return;
            const w = this.size[0];
            const tabW = w / this._tabs.length;

            ctx.save();
            ctx.font = "bold 13px sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            this._tabs.forEach((tab, i) => {
                const x = i * tabW;
                const active = this._tab === tab.id;

                // Background
                ctx.fillStyle = active ? "#5a3d8a" : "#333";
                ctx.fillRect(x, 0, tabW, TAB_H);

                // Border
                ctx.strokeStyle = active ? "#a78bfa" : "#555";
                ctx.lineWidth = active ? 2 : 1;
                ctx.strokeRect(x + 0.5, 0.5, tabW - 1, TAB_H - 1);

                // Label
                ctx.fillStyle = active ? "#fff" : "#bbb";
                ctx.fillText(tab.label, x + tabW / 2, TAB_H / 2);
            });
            ctx.restore();
        };

        // Click handling
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
                if (raceOnly.includes(w.name)) w.hidden = this._tab !== "race";
                if (clothesOnly.includes(w.name)) w.hidden = this._tab !== "clothes";
            }
            // Recompute size so hidden widgets don't leave empty space
            this.setSize(this.computeSize());
        };

        // Initial apply
        setTimeout(() => node._applyVisibility?.(), 150);
    }
});
