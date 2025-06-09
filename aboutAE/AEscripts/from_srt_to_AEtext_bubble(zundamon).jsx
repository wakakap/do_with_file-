// 选择srt文件，根据其中的时间戳导入AE当前合成形成文本图层，动画为冒泡动态效果
// 注意要修改FONT_NAME
// 问题，srt最后一行的文本识别有问题，手动多打一个空行
(function main() {
    // --- Configuration ---
    //Tanuki-Permanent-Marker,LXGWWenKai-Light
    var FONT_NAME = 'LXGWWenKai-Light'; 
    var ANIMATION_DURATION = 0.12; 
    var APPEAR_OVERDRIVE_SCALE = 110; 
    var TEXT_FONT_SIZE = 70;
    var MIN_HOLD_DURATION = 0.01; // 字幕内容以100%大小稳定显示的最短时间 (针对SRT中时长极短或无效的情况)

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

    var srtFile = File.openDialog("请选择一个 .srt 字幕文件", "*.srt", false);
    if (!srtFile) {
        alert("未选择文件，脚本已取消。");
        return;
    }
    srtFile.encoding = "UTF-8";
    srtFile.open("r");
    var srtContent = srtFile.read();
    srtFile.close();

    var srtRegex = /(\d+)\r?\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\r?\n([\s\S]*?)(?=\r?\n\r?\n\d+|\r?\n\d+\r?\n|$)/g;
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

    app.beginUndoGroup("导入SRT字幕并创建表达式动画 (V2.1)");
    var compCenter = [comp.width / 2, comp.height / 2];

    for (var i = 0; i < subtitles.length; i++) {
        var sub = subtitles[i];
        var layerName = "Subtitle " + sub.id;
        var textContent = sub.text;
        var textColor = [1, 1, 1]; // Default to white [R, G, B] in 0-1 range

        // Check if text starts with "r:" for red color
        if (textContent.toLowerCase().indexOf("r:") === 0) {
            textColor = [1, 0, 0]; // Set to red
            textContent = textContent.substring(2); // Remove "r:"
        }

        var layerActualInPoint = sub.startTime;
        var layerActualOutPoint = sub.endTime;
        
        // 确保 SRT 时间戳有效，如果开始时间为负，则将其平移到0开始
        if (layerActualInPoint < 0) {
            // alert("Warning: Subtitle " + sub.id + " starts at a negative time. Shifting to 0."); // 可选的警告
            layerActualOutPoint = layerActualOutPoint - layerActualInPoint; // 保持时长
            layerActualInPoint = 0;
        }

        // 处理SRT中无效或过短的字幕时长
        // 动画总共需要 2 * ANIMATION_DURATION。如果SRT时长不足，动画会重叠。
        // 如果SRT时长为0或负，则强制设定一个最小图层时长，保证动画能播放且有极短的稳定期。
        if (layerActualOutPoint - layerActualInPoint < (2 * ANIMATION_DURATION + MIN_HOLD_DURATION)) {
            if (layerActualOutPoint <= layerActualInPoint) { // SRT条目时长为0或负
                // $.writeln("Warning: Subtitle " + sub.id + " in SRT has zero or negative duration. Adjusting to minimal valid duration."); // 在ESTK中可见
                layerActualOutPoint = layerActualInPoint + (2 * ANIMATION_DURATION) + MIN_HOLD_DURATION;
            }
            // 如果SRT时长大于0但小于 (2*ANIMATION_DURATION + MIN_HOLD_DURATION)，我们仍然使用SRT的时长。
            // 表达式会自动处理动画重叠的情况。
        }
         // 最终安全检查，确保出点在入点之后
        if (layerActualOutPoint <= layerActualInPoint) {
            layerActualOutPoint = layerActualInPoint + 0.001; // 设置一个极小的正时长
        }


        var textLayer = comp.layers.addText(textContent);
        textLayer.name = layerName;
        textLayer.inPoint = layerActualInPoint;
        textLayer.outPoint = layerActualOutPoint;

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
        textDocument.tracking = -90; // 设置字间距为 -100
        textDocument.applyStroke = true; // 启用描边
        textDocument.strokeWidth = 1; // 设置描边宽度为 1 像素
        textDocument.strokeOverFill = true; // 设置描边在填充之上
        // 如果需要设置描边颜色，可以在这里添加，例如：
        // textDocument.strokeColor = [0, 0, 0]; // 黑色描边
        textProp.setValue(textDocument);

        // --- Centering Layer ---
        // sourceRectAtTime 需要一个在图层激活时间内的任意时刻即可，因为我们获取的是未变换的源尺寸。
        // 选择 layerActualInPoint (图层开始时间) 是简单且安全的。
        var tempTimeForRect = layerActualInPoint;

        var sourceRect = textLayer.sourceRectAtTime(tempTimeForRect, false); // false表示获取源素材的原始大小
        var textAnchorPoint = [sourceRect.left + sourceRect.width / 2, sourceRect.top + sourceRect.height / 2];
        textLayer.property("Transform").property("Anchor Point").setValue(textAnchorPoint);
        textLayer.property("Transform").property("Position").setValue(compCenter);

        // --- Apply Scale Expression ---
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
            "    var appearMidTime = animDuration * 0.7;",
            "    if (t < appearMidTime) {",
            "        ease(t, 0, appearMidTime, noScale, [overdriveScale, overdriveScale]);",
            "    } else {",
            "        ease(t, appearMidTime, animDuration, [overdriveScale, overdriveScale], fullScale);",
            "    }",
            "} ",
            "// Disappearance Phase",
            "else if (t > layerDuration - animDuration && t <= layerDuration + 0.0001) { // 加一点点容差确保最后一帧正确",
            "    var timeIntoDisappear = t - (layerDuration - animDuration);",
            "    ease(timeIntoDisappear, 0, animDuration, fullScale, noScale);",
            "} ",
            "// Hold Phase",
            "else if (t >= animDuration && t <= layerDuration - animDuration) {",
            "    fullScale;",
            "} ",
            "// Outside active range or if layerDuration is too short for a hold phase",
            "else {",
            "    if (layerDuration < animDuration) noScale; // If layer is shorter than one animation cycle, default to noScale outside anim.",
            "    else if (t > animDuration && layerDuration < 2 * animDuration) fullScale; // If between one and two anim cycles, hold fullScale briefly.",
            "    else noScale; // Default for safety, though prior conditions should cover.",
            "}"
        ].join("\n");

        scaleProp.expression = scaleExpression;
    }

    app.endUndoGroup();
    alert("SRT字幕导入并创建表达式动画 (V2.1) 完成！\n共创建 " + subtitles.length + " 个文本图层。");

})();