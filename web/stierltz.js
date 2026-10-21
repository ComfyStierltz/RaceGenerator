import { app } from "../../../scripts/app.js";

const TAB_H = 36;
const SOCKET_AREA = 50; // space reserved for output sockets at top

app.registerExtension({
    name: "stierltz.RaceClothesTabs",

    async nodeCreated(node) {
        if (node.comfyClass !== "StierltzRaceClothes") return;

        node._tab = "race";
        node._tabs = [
            { id: "race", label: "Race" },
            { id: "clothes", label: "Clothes" }
        ];

        // Fixed height so tabs don't jump
        const origComputeSize = node.computeSize;
        node.computeSize = function () {
            const size = origComputeSize ? origComputeSize.apply(this, arguments) : [340, 200];
            // Force minimum height so content area is stable
            size[1] = Math.max(size[1], 320);
            return size;
        };

        const origDraw = node.onDrawForeground;
        node.onDrawForeground = function (ctx) {
            // Draw tabs BELOW the socket area
            if (this._tabs) {
                const w = this.size[0];
                const tabW = w / this._tabs.length;
                const y = SOCKET_AREA;
                ctx.save();
                ctx.font = "bold 14px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                this._tabs.forEach((tab, i) => {
                    const x = i * tabW;
                    const active = this._tab === tab.id;
                    ctx.fillStyle = active ? "#5a3d8a" : "#2a2a2a";
                    ctx.fillRect(x, y, tabW, TAB_H);
                    ctx.strokeStyle = active ? "#c4b5fd" : "#555";
                    ctx.lineWidth = active ? 2 : 1;
                    ctx.strokeRect(x + 0.5, y + 0.5, tabW - 1, TAB_H - 1);
                    ctx.fillStyle = active ? "#fff" : "#aaa";
                    ctx.fillText(tab.label, x + tabW / 2, y + TAB_H / 2);
                });
                ctx.restore();
            }
            if (origDraw) origDraw.apply(this, arguments);
        };

        const origMouse = node.onMouseDown;
        node.onMouseDown = function (e, localPos) {
            if (localPos && localPos[1] >= SOCKET_AREA && localPos[1] < SOCKET_AREA + TAB_H && this._tabs) {
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
            // Keep size stable
            this.setSize(this.computeSize());
        };

        setTimeout(() => node._applyVisibility?.(), 100);
    }
});
