import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "stierltz.RaceClothesTabs",

    async nodeCreated(node) {
        if (node.comfyClass !== "StierltzRaceClothes") return;

        // Create container div
        const container = document.createElement("div");
        container.style.cssText = `
            position: absolute;
            background: #2a2a2a;
            border: 1px solid #555;
            border-radius: 6px;
            padding: 4px;
            z-index: 10;
            font-family: sans-serif;
            font-size: 13px;
            pointer-events: auto;
        `;

        // Tab bar
        const tabBar = document.createElement("div");
        tabBar.style.cssText = "display: flex; gap: 4px; margin-bottom: 6px;";
        const raceBtn = document.createElement("button");
        const clothesBtn = document.createElement("button");
        [raceBtn, clothesBtn].forEach(b => {
            b.style.cssText = "flex:1; padding:6px 8px; border:none; border-radius:4px; cursor:pointer; background:#444; color:#ccc;";
        });
        raceBtn.textContent = "Race";
        clothesBtn.textContent = "Clothes";
        tabBar.appendChild(raceBtn);
        tabBar.appendChild(clothesBtn);
        container.appendChild(tabBar);

        // Content area
        const content = document.createElement("div");
        content.style.cssText = "min-height: 120px;";
        container.appendChild(content);

        document.body.appendChild(container);

        node._tab = "race";
        node._container = container;

        const updateContent = () => {
            content.innerHTML = "";
            const active = node._tab === "race";
            raceBtn.style.background = active ? "#5a3d8a" : "#444";
            raceBtn.style.color = active ? "#fff" : "#ccc";
            clothesBtn.style.background = !active ? "#5a3d8a" : "#444";
            clothesBtn.style.color = !active ? "#fff" : "#ccc";

            if (node._tab === "race") {
                content.innerHTML = `
                    <div style="margin:4px 0;"><label>Race:</label> <span>${node.widgets?.find(w=>w.name==="race")?.value || "none"}</span></div>
                    <div style="margin:4px 0;"><label>Gender:</label> <span>${node.widgets?.find(w=>w.name==="gender_male")?.value ? "male" : "female"}</span></div>
                    <div style="margin:4px 0; font-size:11px; color:#888;">(edit in node widgets below)</div>
                `;
            } else {
                content.innerHTML = `
                    <div style="margin:4px 0;"><label>Clothes:</label> <span>${node.widgets?.find(w=>w.name==="clothes")?.value || "none"}</span></div>
                    <div style="margin:4px 0; font-size:11px; color:#888;">(edit in node widgets below)</div>
                `;
            }
        };

        raceBtn.onclick = () => { node._tab = "race"; updateContent(); node._applyVisibility(); };
        clothesBtn.onclick = () => { node._tab = "clothes"; updateContent(); node._applyVisibility(); };

        node._applyVisibility = function () {
            const raceOnly = ["race", "gender_male", "race_positive", "race_negative"];
            const clothesOnly = ["clothes", "clothes_positive"];
            for (const w of this.widgets || []) {
                if (raceOnly.includes(w.name)) w.hidden = this._tab !== "race";
                if (clothesOnly.includes(w.name)) w.hidden = this._tab !== "clothes";
            }
            this.setSize(this.computeSize());
        };

        // Position container relative to node
        const updatePos = () => {
            if (!node.pos || !app.canvas) return;
            const scale = app.canvas.ds?.scale || 1;
            const offset = app.canvas.ds?.offset || [0, 0];
            const x = (node.pos[0] + offset[0]) * scale;
            const y = (node.pos[1] + offset[1] + 60) * scale; // below title + sockets
            container.style.left = x + "px";
            container.style.top = y + "px";
            container.style.width = (node.size[0] * scale - 16) + "px";
        };

        // Hook into canvas draw to keep position in sync
        const origDraw = node.onDrawForeground;
        node.onDrawForeground = function (ctx) {
            updatePos();
            if (origDraw) origDraw.apply(this, arguments);
        };

        updateContent();
        setTimeout(() => { updatePos(); node._applyVisibility?.(); }, 200);

        // Cleanup on remove
        const origOnRemoved = node.onRemoved;
        node.onRemoved = function () {
            container.remove();
            if (origOnRemoved) origOnRemoved.apply(this, arguments);
        };
    }
});
