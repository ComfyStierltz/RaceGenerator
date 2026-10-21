import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "stierltz.RaceClothesTabs",

    async nodeCreated(node) {
        if (node.comfyClass !== "StierltzRaceClothes") return;

        const container = document.createElement("div");
        container.style.cssText = `
            position: absolute; background: #1a1a1a; border: 1px solid #444;
            border-radius: 4px; padding: 8px; z-index: 5;
            font-family: sans-serif; font-size: 12px; color: #ddd;
            pointer-events: auto; box-sizing: border-box;
        `;

        const tabBar = document.createElement("div");
        tabBar.style.cssText = "display:flex; gap:4px; margin-bottom:8px;";
        const raceBtn = document.createElement("button");
        const clothesBtn = document.createElement("button");
        const styleBtn = (b, active) => {
            b.style.cssText = `flex:1; padding:6px; border:none; border-radius:3px; cursor:pointer;
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

        const api = async (path, opts) => {
            try {
                const r = await fetch(path, opts);
                if (r.ok) return await r.json();
            } catch(e) { console.warn("[stierltz]", e); }
            return {};
        };

        const refreshClothesOptions = async () => {
            const list = await api("/stierltz/list");
            const clothesW = getW("clothes");
            if (clothesW && list.clothes) {
                clothesW.options.values = ["none", ...list.clothes];
            }
        };

        const render = async () => {
            const isRace = node._tab === "race";
            styleBtn(raceBtn, isRace);
            styleBtn(clothesBtn, !isRace);
            content.innerHTML = "";

            const raceW = getW("race");
            const genderW = getW("gender_male");
            const posW = getW("race_positive");
            const negW = getW("race_negative");
            const clothesW = getW("clothes");
            const cposW = getW("clothes_positive");
            const cnegW = getW("clothes_negative");

            const gender = genderW?.value ? "male" : "female";

            if (isRace) {
                const raceName = raceW?.value || "none";
                const data = await api(`/stierltz/race/${raceName}`);
                const gPos = data[`${gender}_positive`] || data.positive || "";
                const gNeg = data[`${gender}_negative`] || data.negative || "";
                if (posW) posW.value = gPos;
                if (negW) negW.value = gNeg;

                content.innerHTML = `
                    <div style="margin-bottom:6px;"><label style="font-size:11px;color:#aaa;">Race</label>
                        <select id="st_race" style="width:100%;background:#2a2a2a;color:#fff;border:1px solid #555;padding:4px;border-radius:3px;"></select></div>
                    <div style="margin-bottom:6px;"><label style="font-size:12px;"><input type="checkbox" id="st_gender"> Male</label></div>
                    <div style="margin-bottom:6px;"><label style="font-size:11px;color:#aaa;">Positive (${gender})</label>
                        <textarea id="st_rpos" rows="3" style="width:100%;background:#2a2a2a;color:#fff;border:1px solid #555;border-radius:3px;resize:vertical;font-size:11px;"></textarea></div>
                    <div style="margin-bottom:6px;"><label style="font-size:11px;color:#aaa;">Negative (${gender})</label>
                        <textarea id="st_rneg" rows="2" style="width:100%;background:#2a2a2a;color:#fff;border:1px solid #555;border-radius:3px;resize:vertical;font-size:11px;"></textarea></div>
                    <button id="st_new_race" style="width:100%;padding:5px;background:#3a5a3a;color:#fff;border:none;border-radius:3px;cursor:pointer;">+ New Race</button>
                `;
                const sel = content.querySelector("#st_race");
                if (raceW && sel) {
                    (raceW.options?.values || ["none"]).forEach(v => {
                        const o = document.createElement("option");
                        o.value = v; o.textContent = v;
                        if (v === raceW.value) o.selected = true;
                        sel.appendChild(o);
                    });
                    sel.onchange = async () => { raceW.value = sel.value; await render(); };
                }
                const cb = content.querySelector("#st_gender");
                if (genderW && cb) {
                    cb.checked = !!genderW.value;
                    cb.onchange = async () => { genderW.value = cb.checked; await render(); };
                }
                const tp = content.querySelector("#st_rpos");
                if (tp) { tp.value = gPos; tp.oninput = () => { if (posW) posW.value = tp.value; }; }
                const tn = content.querySelector("#st_rneg");
                if (tn) { tn.value = gNeg; tn.oninput = () => { if (negW) negW.value = tn.value; }; }
                content.querySelector("#st_new_race").onclick = async () => {
                    const name = prompt("New race name:");
                    if (!name) return;
                    const pos = content.querySelector("#st_rpos").value;
                    const neg = content.querySelector("#st_rneg").value;
                    await api(`/stierltz/save_race`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({name, positive:pos, negative:neg, gender})});
                    alert("Saved: " + name);
                };
            } else {
                const clothesName = clothesW?.value || "none";
                const data = await api(`/stierltz/clothes/${clothesName}`);
                if (cposW) cposW.value = data.positive || "";
                if (cnegW) cnegW.value = data.negative || "";

                content.innerHTML = `
                    <div style="margin-bottom:6px;"><label style="font-size:11px;color:#aaa;">Clothes</label>
                        <select id="st_clothes" style="width:100%;background:#2a2a2a;color:#fff;border:1px solid #555;padding:4px;border-radius:3px;"></select></div>
                    <div style="margin-bottom:6px;"><label style="font-size:11px;color:#aaa;">Clothes Positive</label>
                        <textarea id="st_cpos" rows="2" style="width:100%;background:#2a2a2a;color:#fff;border:1px solid #555;border-radius:3px;resize:vertical;font-size:11px;"></textarea></div>
                    <div style="margin-bottom:6px;"><label style="font-size:11px;color:#aaa;">Clothes Negative</label>
                        <textarea id="st_cneg" rows="2" style="width:100%;background:#2a2a2a;color:#fff;border:1px solid #555;border-radius:3px;resize:vertical;font-size:11px;"></textarea></div>
                    <button id="st_new_clothes" style="width:100%;padding:5px;background:#3a5a3a;color:#fff;border:none;border-radius:3px;cursor:pointer;">+ New Clothes</button>
                `;
                const sel = content.querySelector("#st_clothes");
                if (clothesW && sel) {
                    (clothesW.options?.values || ["none"]).forEach(v => {
                        const o = document.createElement("option");
                        o.value = v; o.textContent = v;
                        if (v === clothesW.value) o.selected = true;
                        sel.appendChild(o);
                    });
                    sel.onchange = async () => { clothesW.value = sel.value; await render(); };
                }
                const tc = content.querySelector("#st_cpos");
                if (tc) { tc.value = data.positive || ""; tc.oninput = () => { if (cposW) cposW.value = tc.value; }; }
                const tn = content.querySelector("#st_cneg");
                if (tn) { tn.value = data.negative || ""; tn.oninput = () => { if (cnegW) cnegW.value = tn.value; }; }
                content.querySelector("#st_new_clothes").onclick = async () => {
                    const name = prompt("New clothes name:");
                    if (!name) return;
                    const pos = content.querySelector("#st_cpos").value;
                    const neg = content.querySelector("#st_cneg").value;
                    const result = await api(`/stierltz/save_clothes`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({name, positive:pos, negative:neg})});
                    if (result.list && clothesW) {
                        clothesW.options.values = ["none", ...result.list];
                    }
                    await refreshClothesOptions();
                    alert("Saved: " + name);
                    await render();
                };
            }
        };

        raceBtn.onclick = () => { node._tab = "race"; render(); };
        clothesBtn.onclick = () => { node._tab = "clothes"; render(); };

        const hideNative = () => {
            const hide = ["race","clothes","gender_male","race_positive","race_negative","clothes_positive","clothes_negative","tab"];
            for (const w of node.widgets || []) {
                if (hide.includes(w.name)) w.hidden = true;
            }
            node.setSize([Math.max(node.size[0], 340), 500]);
        };

        const updatePos = () => {
            if (!node.pos || !app.canvas) return;
            const scale = app.canvas.ds?.scale || 1;
            const offset = app.canvas.ds?.offset || [0,0];
            const topOffset = 78;
            const x = (node.pos[0] + offset[0]) * scale + 8 * scale;
            const y = (node.pos[1] + offset[1] + topOffset) * scale;
            const w = (node.size[0] - 16) * scale;
            container.style.left = x + "px";
            container.style.top = y + "px";
            container.style.width = Math.max(220, w) + "px";
        };

        const origDraw = node.onDrawForeground;
        node.onDrawForeground = function(ctx) { updatePos(); if (origDraw) origDraw.apply(this, arguments); };
        const origRemoved = node.onRemoved;
        node.onRemoved = function() { container.remove(); if (origRemoved) origRemoved.apply(this, arguments); };

        setTimeout(() => { render(); hideNative(); updatePos(); }, 300);
    }
});
