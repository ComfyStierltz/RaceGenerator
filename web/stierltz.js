import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "stierltz.RaceClothesTabs",

    async nodeCreated(node) {
        if (node.comfyClass !== "StierltzRaceClothes") return;

        const container = document.createElement("div");
        container.style.cssText = `
            position: absolute; background: #1e1e1e; border: 1px solid #555;
            border-radius: 6px; padding: 6px; z-index: 20;
            font-family: sans-serif; font-size: 12px; color: #ddd;
            pointer-events: auto; box-sizing: border-box;
        `;

        const tabBar = document.createElement("div");
        tabBar.style.cssText = "display:flex; gap:4px; margin-bottom:8px;";
        const raceBtn = document.createElement("button");
        const clothesBtn = document.createElement("button");
        const styleBtn = (b, active) => {
            b.style.cssText = `flex:1; padding:6px; border:none; border-radius:4px; cursor:pointer;
                background:${active ? "#5a3d8a" : "#3a3a3a"}; color:${active ? "#fff" : "#aaa"}; font-weight:bold;`;
        };
        raceBtn.textContent = "Race";
        clothesBtn.textContent = "Clothes";
        tabBar.append(raceBtn, clothesBtn);
        container.appendChild(tabBar);

        const content = document.createElement("div");
        container.appendChild(content);
        document.body.appendChild(container);

        node._tab = "race";
        node._container = container;

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
                    <div style="margin-bottom:6px;">
                        <label style="display:block; margin-bottom:2px;">Race</label>
                        <select id="st_race" style="width:100%; background:#333; color:#fff; border:1px solid #555; padding:4px; border-radius:3px;"></select>
                    </div>
                    <div style="margin-bottom:6px;">
                        <label><input type="checkbox" id="st_gender"> Male</label>
                    </div>
                    <div style="margin-bottom:6px;">
                        <label style="display:block; margin-bottom:2px;">Positive</label>
                        <textarea id="st_rpos" rows="3" style="width:100%; background:#333; color:#fff; border:1px solid #555; border-radius:3px; resize:vertical;"></textarea>
                    </div>
                    <div>
                        <label style="display:block; margin-bottom:2px;">Negative</label>
                        <textarea id="st_rneg" rows="2" style="width:100%; background:#333; color:#fff; border:1px solid #555; border-radius:3px; resize:vertical;"></textarea>
                    </div>
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
                if (genderW && cb) {
                    cb.checked = !!genderW.value;
                    cb.onchange = () => { genderW.value = cb.checked; };
                }
                const tp = content.querySelector("#st_rpos");
                if (posW && tp) { tp.value = posW.value || ""; tp.oninput = () => { posW.value = tp.value; }; }
                const tn = content.querySelector("#st_rneg");
                if (negW && tn) { tn.value = negW.value || ""; tn.oninput = () => { negW.value = tn.value; }; }
            } else {
                const clothesW = getW("clothes");
                const cposW = getW("clothes_positive");
                content.innerHTML = `
                    <div style="margin-bottom:6px;">
                        <label style="display:block; margin-bottom:2px;">Clothes</label>
                        <select id="st_clothes" style="width:100%; background:#333; color:#fff; border:1px solid #555; padding:4px; border-radius:3px;"></select>
                    </div>
                    <div>
                        <label style="display:block; margin-bottom:2px;">Clothes Positive</label>
                        <textarea id="st_cpos" rows="3" style="width:100%; background:#333; color:#fff; border:1px solid #555; border-radius:3px; resize:vertical;"></textarea>
                    </div>
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

        raceBtn.onclick = () => { node._tab = "race"; render(); hideNative(); };
        clothesBtn.onclick = () => { node._tab = "clothes"; render(); hideNative(); };

        const hideNative = () => {
            const hide = ["race", "clothes", "gender_male", "race_positive", "race_negative", "clothes_positive"];
            for (const w of node.widgets || []) {
                if (hide.includes(w.name)) w.hidden = true;
            }
            node.setSize(node.computeSize());
        };

        const updatePos = () => {
            if (!node.pos || !app.canvas) return;
            const scale = app.canvas.ds?.scale || 1;
            const offset = app.canvas.ds?.offset || [0, 0];
            const x = (node.pos[0] + offset[0]) * scale + 8;
            const y = (node.pos[1] + offset[1] + 70) * scale;
            container.style.left = x + "px";
            container.style.top = y + "px";
            container.style.width = Math.max(200, (node.size[0] * scale - 24)) + "px";
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

        setTimeout(() => { render(); hideNative(); updatePos(); }, 150);
    }
});
