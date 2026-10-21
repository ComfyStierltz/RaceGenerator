import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "stierltz.raceclothes",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "StierltzRaceClothes") {
            const origOnNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = origOnNodeCreated?.apply(this, arguments);
                // Add a simple refresh button via context menu later if needed
                return r;
            };
        }
    }
});
