// 删除当前合成中的所有文本图层
(function deleteTextLayers() {
    var comp = app.project.activeItem;

    // Check if a composition is active
    if (!comp || !(comp instanceof CompItem)) {
        alert("Please select or open a composition first.");
        return;
    }

    app.beginUndoGroup("Delete All Text Layers"); // Start an undo group

    var layersToDelete = [];

    // Iterate through layers from top to bottom
    // We collect them first because deleting layers shifts their indices
    for (var i = 1; i <= comp.layers.length; i++) {
        var layer = comp.layers[i];
        if (layer instanceof TextLayer) {
            layersToDelete.push(layer);
        }
    }

    // Now delete the collected layers
    if (layersToDelete.length > 0) {
        for (var j = 0; j < layersToDelete.length; j++) {
            layersToDelete[j].remove();
        }
        alert("Deleted " + layersToDelete.length + " text layers from '" + comp.name + "'.");
    } else {
        alert("No text layers found in '" + comp.name + "'.");
    }

    app.endUndoGroup(); // End the undo group
})();