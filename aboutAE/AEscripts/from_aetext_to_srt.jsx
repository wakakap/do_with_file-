// 把当前合成中的文本图层导出做成srt文件
(function main() {
    // --- Helper Function: Convert seconds to SRT time (HH:MM:SS,mmm) ---
    function secondsToSrtTime(totalSeconds) {
        if (isNaN(totalSeconds) || totalSeconds < 0) {
            return "00:00:00,000";
        }

        var hours = Math.floor(totalSeconds / 3600);
        totalSeconds %= 3600;
        var minutes = Math.floor(totalSeconds / 60);
        var seconds = Math.floor(totalSeconds % 60);
        var milliseconds = Math.floor((totalSeconds - Math.floor(totalSeconds)) * 1000);

        // Pad with leading zeros
        var h = (hours < 10 ? "0" : "") + hours;
        var m = (minutes < 10 ? "0" : "") + minutes;
        var s = (seconds < 10 ? "0" : "") + seconds;
        var ms = (milliseconds < 10 ? "00" : (milliseconds < 100 ? "0" : "")) + milliseconds;

        return h + ":" + m + ":" + s + "," + ms;
    }

    // --- Main Logic ---
    var comp = app.project.activeItem;
    if (!comp || !(comp instanceof CompItem)) {
        alert("请先选择或打开一个合成 (Composition)！");
        return;
    }

    var textLayersData = [];

    // Iterate through all layers in the composition
    for (var i = 1; i <= comp.layers.length; i++) {
        var layer = comp.layers[i];

        // Check if the layer is a text layer
        if (layer instanceof TextLayer) {
            try {
                var sourceTextProp = layer.property("Source Text");
                var textDocument = sourceTextProp.value; // Get the TextDocument object for the current frame
                var textContent = textDocument.text; // Get the actual text string

                // Optional: Clean up layer name to use as ID (e.g., "Subtitle 1" -> "1")
                var layerIdMatch = layer.name.match(/(\d+)$/); // Finds numbers at the end of the layer name
                var subtitleId = layerIdMatch ? layerIdMatch[1] : (i).toString(); // Use found ID or layer index

                textLayersData.push({
                    id: parseInt(subtitleId), // Store as number for sorting
                    inPoint: layer.inPoint,
                    outPoint: layer.outPoint,
                    text: textContent
                });
            } catch (e) {
                $.writeln("Skipping text layer '" + layer.name + "' due to error: " + e.toString());
            }
        }
    }

    if (textLayersData.length === 0) {
        alert("当前合成中未找到任何文本图层。");
        return;
    }

    // Sort subtitles by their inPoint to ensure correct order in SRT
    textLayersData.sort(function(a, b) {
        return a.inPoint - b.inPoint;
    });
    
    // Re-number IDs after sorting to ensure sequential IDs in SRT file
    for (var j = 0; j < textLayersData.length; j++) {
        textLayersData[j].id = j + 1;
    }


    var srtContent = [];
    for (var k = 0; k < textLayersData.length; k++) {
        var data = textLayersData[k];
        var startTimeSrt = secondsToSrtTime(data.inPoint);
        var endTimeSrt = secondsToSrtTime(data.outPoint);

        srtContent.push(data.id.toString());
        srtContent.push(startTimeSrt + " --> " + endTimeSrt);
        srtContent.push(data.text);
        srtContent.push(""); // Empty line separates entries
    }

    // Choose save path
    var saveFile = File.saveDialog("保存 SRT 字幕文件", "*.srt");

    if (saveFile) {
        saveFile.open("w", undefined, "UTF-8");
        saveFile.write(srtContent.join("\n"));
        saveFile.close();
        alert("SRT 文件已成功保存到:\n" + saveFile.fsName);
    } else {
        alert("未选择保存路径，SRT 文件未保存。");
    }

})();