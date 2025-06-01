// 指定 WAV_FILES_FOLDER ，选择对应srt文件
// 把一个音频文件夹中的所有形如 0001_*****.wav 的文件导入AE中首尾相接，相隔GAP_BETWEEN_SUBTITLES，然后把对应的srt中的文本也放到对应位置
(function main() {
    // --- Configuration ---
    var FONT_NAME = 'Tanuki-Permanent-Marker';
    var ANIMATION_DURATION = 0.12;
    var APPEAR_OVERDRIVE_SCALE = 110;
    var TEXT_FONT_SIZE = 60;
    var MIN_HOLD_DURATION = 0.01; // 字幕内容以100%大小稳定显示的最短时间 (针对SRT中时长极短或无效的情况)
    var GAP_BETWEEN_SUBTITLES = 0.2; // <<< NEW CONFIGURATION: Gap between subtitles in seconds

    // --- NEW CONFIGURATION: WAV File Import ---
    // IMPORTANT: Set the path to your WAV files folder.
    // Example (Windows): 'C:/Your/Audio/Files/'
    // Example (macOS): '/Users/YourUser/Documents/AudioFiles/'
    // Make sure to use forward slashes for paths.
    var WAV_FILES_FOLDER = 'E:\\抽吧唧\\1\\voice'; // <<< SET YOUR WAV FILES FOLDER PATH HERE!

    // --- Helper Function: Convert SRT time (HH:MM:SS,mmm) to seconds ---
    function srtTimeToSeconds(timeString) {
        try {
            var parts = timeString.split(':');
            var hours = parseFloat(parts[0]);
            var minutes = parseFloat(parts[1]);
            var secondsAndMillis = parts[2].split(',');
            var seconds = parseFloat(secondsAndMillis[0]);
            var milliseconds = parseFloat(secondsAndMillis[1]);
            return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000;
        } catch (e) {
            alert("Error parsing time string: " + timeString + "\n" + e.toString());
            return 0;
        }
    }

    // --- Main Logic ---
    var comp = app.project.activeItem;
    if (!comp || !(comp instanceof CompItem)) {
        alert("请先选择或打开一个合成 (Composition)！");
        return;
    }

    // Check if WAV_FILES_FOLDER is set
    if (WAV_FILES_FOLDER === '') {
        alert("请在脚本配置中设置 'WAV_FILES_FOLDER' 变量为您存放 WAV 文件的文件夹路径！");
        return;
    }

    var wavFolder = new Folder(WAV_FILES_FOLDER);
    if (!wavFolder.exists) {
        alert("指定的 WAV 文件文件夹不存在：\n" + WAV_FILES_FOLDER + "\n请检查路径是否正确。");
        return;
    }

    var srtFile = File.openDialog("请选择一个 .srt 字幕文件", "*.srt", false);
    if (!srtFile) {
        alert("未选择文件，脚本已取消。");
        return;
    }

    srtFile.open("r");
    var srtContent = srtFile.read();
    srtFile.close();

    var srtRegex = /(\d+)\s*(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*([\s\S]*?)(?=\n\n|\n\d+\n|$)/g;
    var match;
    var subtitles = [];

    while ((match = srtRegex.exec(srtContent)) !== null) {
        subtitles.push({
            id: match[1],
            startTime: srtTimeToSeconds(match[2]),
            endTime: srtTimeToSeconds(match[3]),
            text: match[4].replace(/^\s+|\s+$/g, '')
        });
    }

    if (subtitles.length === 0) {
        alert("未能从文件中解析出任何字幕条目，请检查SRT文件格式。");
        return;
    }

    app.beginUndoGroup("导入SRT字幕、表达式动画和WAV导入 (V2.4 - WAV Timed with Gap)");
    var compCenter = [comp.width / 2, comp.height / 2];
    var currentTime = 0; // Initialize current time for sequential placement

    for (var i = 0; i < subtitles.length; i++) {
        var sub = subtitles[i];
        var textContent = sub.text;
        var textColor = [1, 1, 1]; // Default to white [R, G, B] in 0-1 range

        // Check if text starts with "r:" for red color
        if (textContent.toLowerCase().indexOf("r:") === 0) {
            textColor = [1, 0, 0]; // Set to red
            textContent = textContent.substring(2); // Remove "r:"
        }

        // --- Import WAV File FIRST ---
        var formattedId = ("0000" + sub.id).slice(-4);
        var expectedWavFilenamePattern = formattedId + "*.wav";
        var foundWavFiles = wavFolder.getFiles(expectedWavFilenamePattern);
        var audioLayer = null;
        var wavDuration = 0;

        // Apply gap before placing the first audio/text layer, unless it's the very first one
        if (i > 0) {
            currentTime += GAP_BETWEEN_SUBTITLES;
        }

        if (foundWavFiles.length > 0) {
            var wavFileToImport = null;
            var exactMatchFilename = formattedId + ".wav";

            for (var k = 0; k < foundWavFiles.length; k++) {
                if (foundWavFiles[k].name.toLowerCase() === exactMatchFilename.toLowerCase()) {
                    wavFileToImport = foundWavFiles[k];
                    break;
                }
            }
            if (wavFileToImport === null) {
                wavFileToImport = foundWavFiles[0]; // If no exact match, use the first one that starts with the ID
            }

            var importOptions = new ImportOptions(wavFileToImport);
            if (importOptions.canImportAs(ImportAsType.FOOTAGE)) {
                try {
                    var importedFootage = app.project.importFile(importOptions);
                    audioLayer = comp.layers.add(importedFootage);
                    audioLayer.name = "Audio " + sub.id;
                    audioLayer.startTime = currentTime; // Place audio layer sequentially
                    wavDuration = importedFootage.duration;
                    // Ensure minimum duration for very short audio clips for visibility
                    if (wavDuration < (2 * ANIMATION_DURATION + MIN_HOLD_DURATION)) {
                        wavDuration = (2 * ANIMATION_DURATION + MIN_HOLD_DURATION);
                    }
                } catch (importError) {
                    alert("导入 WAV 文件 '" + wavFileToImport.name + "' 时发生错误: " + importError.toString());
                    wavDuration = (2 * ANIMATION_DURATION + MIN_HOLD_DURATION); // Fallback duration if import fails
                }
            } else {
                alert("文件 '" + wavFileToImport.name + "' 无法作为素材导入。");
                wavDuration = (2 * ANIMATION_DURATION + MIN_HOLD_DURATION); // Fallback duration
            }
        } else {
            $.writeln("Warning: No matching WAV file found for subtitle " + sub.id + " with pattern " + expectedWavFilenamePattern + " in " + WAV_FILES_FOLDER + ". Text layer will use a default duration.");
            wavDuration = (2 * ANIMATION_DURATION + MIN_HOLD_DURATION); // Assign a default duration if no WAV found
        }

        // --- Create Text Layer based on WAV timing ---
        var layerInPoint = currentTime;
        var layerOutPoint = currentTime + wavDuration;

        var textLayer = comp.layers.addText(textContent);
        textLayer.name = "Subtitle " + sub.id;
        textLayer.inPoint = layerInPoint;
        textLayer.outPoint = layerOutPoint;

        // If audio layer was created, place text layer directly above it.
        if (audioLayer !== null) {
            textLayer.moveAfter(audioLayer);
        }

        // --- Text Properties ---
        var textProp = textLayer.property("Source Text");
        var textDocument = textProp.value;
        try {
            textDocument.font = FONT_NAME;
        } catch (fontError) {
            alert("设置字体 '" + FONT_NAME + "' 时发生错误: " + fontError.toString() + "\n请检查字体名称和脚本文件编码 (应为UTF-8)。\n将尝试使用默认字体。");
        }
        textDocument.fontSize = TEXT_FONT_SIZE;
        textDocument.justification = ParagraphJustification.CENTER_JUSTIFY;
        textDocument.fillColor = textColor; // Set text color here
        textDocument.leading = 80; // 设置行高为 80 像素
        textDocument.tracking = -100; // 设置字间距为 -100
        textDocument.applyStroke = true; // 启用描边
        textDocument.strokeWidth = 1; // 设置描边宽度为 1 像素
        textDocument.strokeOverFill = true; // 设置描边在填充之上
        textProp.setValue(textDocument);

        // --- Centering Layer ---
        var tempTimeForRect = layerInPoint;
        var sourceRect = textLayer.sourceRectAtTime(tempTimeForRect, false);
        var textAnchorPoint = [sourceRect.left + sourceRect.width / 2, sourceRect.top + sourceRect.height / 2];
        textLayer.property("Transform").property("Anchor Point").setValue(textAnchorPoint);
        textLayer.property("Transform").property("Position").setValue(compCenter);

        // --- Apply Scale Expression (remains the same) ---
        var scaleProp = textLayer.property("Transform").property("Scale");

        var scaleExpression = [
            "// SRT Text Layer Scale Animation Expression v2.1",
            "var animDuration = " + ANIMATION_DURATION.toFixed(3) + ";",
            "var overdriveScale = " + APPEAR_OVERDRIVE_SCALE.toFixed(3) + ";",
            "var fullScale = [100, 100];",
            "var noScale = [0, 0];",
            "",
            "var t = time - thisLayer.inPoint;",
            "var layerDuration = thisLayer.outPoint - thisLayer.inPoint;",
            "",
            "// Appearance Phase",
            "if (t >= 0 && t < animDuration) {",
            "   var appearMidTime = animDuration * 0.7;",
            "   if (t < appearMidTime) {",
            "       ease(t, 0, appearMidTime, noScale, [overdriveScale, overdriveScale]);",
            "   } else {",
            "       ease(t, appearMidTime, animDuration, [overdriveScale, overdriveScale], fullScale);",
            "   }",
            "} ",
            "// Disappearance Phase",
            "else if (t > layerDuration - animDuration && t <= layerDuration + 0.0001) { // 加一点点容差确保最后一帧正确",
            "   var timeIntoDisappear = t - (layerDuration - animDuration);",
            "   ease(timeIntoDisappear, 0, animDuration, fullScale, noScale);",
            "} ",
            "// Hold Phase",
            "else if (t >= animDuration && t <= layerDuration - animDuration) {",
            "   fullScale;",
            "} ",
            "// Outside active range or if layerDuration is too short for a hold phase",
            "else {",
            "   if (layerDuration < animDuration) noScale; // If layer is shorter than one animation cycle, default to noScale outside anim.",
            "   else if (t > animDuration && layerDuration < 2 * animDuration) fullScale; // If between one and two anim cycles, hold fullScale briefly.",
            "   else noScale; // Default for safety, though prior conditions should cover.",
            "}"
        ].join("\n");

        scaleProp.expression = scaleExpression;

        // Update currentTime for the next sequential layer, including the gap
        currentTime = layerOutPoint;
    }

    app.endUndoGroup();
    alert("SRT字幕导入、表达式动画和WAV导入 (V2.4 - WAV Timed with Gap) 完成！\n共创建 " + subtitles.length + " 个文本图层和对应的音频图层（如果找到）。");

})();