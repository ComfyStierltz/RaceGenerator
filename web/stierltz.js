import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "stierltz.RaceClothesTabs",

    async nodeCreated(node) {
        if (node.comfyClass !== "StierltzRaceClothes") return;

        const container = document.createElement("div");
        container.style.cssText = `
            position: absolute; background: #1a1a1a; border: 1px solid #444;
            border-radius: 4px; padding: 6px; z-index: 5;
            font-family: sans-serif; font-size: 12px; color: #ddd;
            pointer-events: auto; box-sizing: border-box; overflow: hidden;
        `;

        const tabBar = document.createElement("div");
        tabBar.style.cssText = "display:flex; gap:4px; margin-bottom:6px;";
        const raceBtn = document.createElement("button");
        const clothesBtn = document.createElement("button");
        const styleBtn = (b, active) => {
            b.style.cssText = `flex:1; padding:5px; border:none; border-radius:3px; cursor:pointer;
                background:${active ? "#5a3d8a" : "#333"}; color:${active ? "#fff" : "#aaa"}; font-weight:bold; font-size:12px;`;
        };
        raceBtn.textContent = "Race";
        clothesBtn.textContent = "Clothes";
        tabBar.append(raceBtn, clothesBtn);
        container.appendChild(tabBar);

        const content = document.createElement("div");
        container.appendChild(content);
        document.body.appendChild(container);

        node._tab = "race";

        const getW = (name) => node.widgets?.find(w => w.name === name);

        const render = () => {
            content.innerHTML = "";
            const isRace = node._tab === "race";
            styleBtn(raceBtn, isRace);
            styleBtn(clothesBtn, !isRace);

            if (isRace) {
                const raceW = getW("race");
                const genderW = getW("gender_male");
                const posW = getW("race_positive");
                const negW = getW("race_negative");
                content.innerHTML = `
                    <div style="margin-bottom:4px;"><label style="font-size:11px;">Race</label>
                        <select id="st_race" style="width:100%;background:#2a2a2a;color:#fff;border:1px solid #555;padding:3px;border-radius:3px;"></select></div>
                    <div style="margin-bottom:4px;"><label style="font-size:11px;"><input type="checkbox" id="st_gender"> Male</label></div>
                    <div style="margin-bottom:4px;"><label style="font-size:11px;">Positive</label>
                        <textarea id="st_rpos" rows="2" style="width:100%;background:#2a2a2a;color:#fff;border:1px solid #555;border-radius:3px;resize:vertical;font-size:11px;"></textarea></div>
                    <div><label style="font-size:11px;">Negative</label>
                        <textarea id="st_rneg" rows="2" style="width:100%;background:#2a2a2a;color:#fff;border:1px solid #555;border-radius:3px;resize:vertical;font-size:11px;"></textarea></div>
                `;
                const sel = content.querySelector("#st_race");
                if (raceW && sel) {
                    (raceW.options?.values || ["none"]).forEach(v => {
                        const o = document.createElement("option");
                        o.value = v; o.textContent = v;
                        if (v === raceW.value) o.selected = true;
                        sel.appendChild(o);
                    });
                    sel.onchange = () => { raceW.value = sel.value; };
                }
                const cb = content.querySelector("#st_gender");
                if (genderW && cb) { cb.checked = !!genderW.value; cb.onchange = () => { genderW.value = cb.checked; }; }
                const tp = content.querySelector("#st_rpos");
                if (posW && tp) { tp.value = posW.value || ""; tp.oninput = () => { posW.value = tp.value; }; }
                const tn = content.querySelector("#st_rneg");
                if (negW && tn) { tn.value = negW.value || ""; tn.oninput = () => { negW.value = tn.value; }; }
            } else {
                const clothesW = getW("clothes");
                const cposW = getW("clothes_positive");
                content.innerHTML = `
                    <div style="margin-bottom:4px;"><label style="font-size:11px;">Clothes</label>
                        <select id="st_clothes" style="width:100%;background:#2a2a2a;color:#fff;border:1px solid #555;padding:3px;border-radius:3px;"></select></div>
                    <div><label style="font-size:11px;">Clothes Positive</label>
                        <textarea id="st_cpos" rows="2" style="width:100%;background:#2a2a2a;color:#fff;border:1px solid #555;border-radius:3px;resize:vertical;font-size:11px;"></textarea></div>
                `;
                const sel = content.querySelector("#st_clothes");
                if (clothesW && sel) {
                    (clothesW.options?.values || ["none"]).forEach(v => {
                        const o = document.createElement("option");
                        o.value = v; o.textContent = v;
                        if (v === clothesW.value) o.selected = true;
                        sel.appendChild(o);
                    });
                    sel.onchange = () => { clothesW.value = sel.value; };
                }
                const tc = content.querySelector("#st_cpos");
                if (cposW && tc) { tc.value = cposW.value || ""; tc.oninput = () => { cposW.value = tc.value; }; }
            }
        };

        raceBtn.onclick = () => { node._tab = "race"; render(); };
        clothesBtn.onclick = () => { node._tab = "clothes"; render(); };

        // Hide native widgets so only the div shows
        const hideNative = () => {
            const hide = ["race", "clothes", "gender_male", "race_positive", "race_negative", "clothes_positive", "tab"];
            for (const w of node.widgets || []) {
                if (hide.includes(w.name)) w.hidden = true;
            }
            // Shrink node to just title + sockets + our overlay
            node.setSize([node.size[0], 90]);
        };

        const updatePos = () => {
            if (!node.pos || !app.canvas) return;
            const scale = app.canvas.ds?.scale || 1;
            const offset = app.canvas.ds?.offset || [0, 0];
            // Position inside the node, below title bar (~28px) and sockets
            const titleH = 28;
            const x = (node.pos[0] + offset[0]) * scale + 6 * scale;
            const y = (node.pos[1] + offset[1] + titleH + 8) * scale;
            const w = (node.size[0] - 12) * scale;
            container.style.left = x + "px";
            container.style.top = y + "px";
            container.style.width = Math.max(180, w) + "px";
        };

        const origDraw = node.onDrawForeground;
        node.onDrawForeground = function (ctx) {
            updatePos();
            if (origDraw) origDraw.apply(this, arguments);
        };

        const origRemoved = node.onRemoved;
        node.onRemoved = function () {
            container.remove();
            if (origRemoved) origRemoved.apply(this, arguments);
        };

        setTimeout(() => { render(); hideNative(); updatePos(); }, 100);
    }
});
