(function main() {
    // --- Configuration ---
    var FONT_NAME = 'LXGWWenKai-Light'; // 字体名称
    var ANIMATION_DURATION = 0.12;
    var APPEAR_OVERDRIVE_SCALE = 110;
    var TEXT_FONT_SIZE = 70;
    var MIN_HOLD_DURATION = 0.01; // This might be less relevant now that SRT dictates timing, but kept for text animation calculation.
    var GAP_BETWEEN_SUBTITLES = 0.2; // This is no longer used for sequential placement but could be for other purposes if needed.

    // --- (新) 定义嘴型和眼睛的表达式字符串 ---
    var bigMouthExpression = "var threshold = 2.0; // 阈值\n" +
        "var onDuration = 0.1; // 大嘴时长\n" +
        "var halfDuration = 0.06; // 中嘴时长\n" +
        "var offDuration = 0.18; // 闭嘴时长\n" +
        "var cutDuration = onDuration; // 收尾动画的截止时长参数1\n" +
        "var cutDuration2 = halfDuration // 收尾动画的截止时长参数1\n" +
        "\n" +
        "var frame = thisComp.frameDuration;\n" +
        "var amplitude = thisComp.layer(\"音频振幅\").effect(\"两个通道\")(\"滑块\");\n" +
        "var loopDuration = onDuration + halfDuration + offDuration + halfDuration; // 大->小->闭->小\n" +
        "\n" +
        "var eventStartTime = -1;\n" +
        "var eventEndTime = -1;\n" +
        "var inEvent = (amplitude.valueAtTime(time) > threshold);\n" +
        "\n" +
        "if (inEvent) {\n" +
        "    var t = time;\n" +
        "    while (t >= 0) { if (amplitude.valueAtTime(t) > threshold) { t -= frame; } else { break; } }\n" +
        "    eventStartTime = t + frame;\n" +
        "} else {\n" +
        "    var t = time - frame;\n" +
        "    var foundEvent = false;\n" +
        "    while (t >= 0) { if (amplitude.valueAtTime(t) > threshold) { eventEndTime = t; foundEvent = true; break; } t -= frame; }\n" +
        "    if (foundEvent) {\n" +
        "        var t2 = eventEndTime;\n" +
        "        while (t2 >= 0) { if (amplitude.valueAtTime(t2) > threshold) { t2 -= frame; } else { break; } }\n" +
        "        eventStartTime = t2 + frame;\n" +
        "    }\n" +
        "}\n" +
        "\n" +
        "var finalOpacity = 0;\n" +
        "if (eventStartTime !== -1) {\n" +
        "    var blinkingClock = time - eventStartTime;\n" +
        "    var idealOpacity = (blinkingClock % loopDuration < onDuration) ? 100 : 0;\n" +
        "\n" +
        "    if (inEvent) {\n" +
        "        finalOpacity = idealOpacity;\n" +
        "    } else { // 声音停止，进入收尾判断逻辑\n" +
        "        var totalEventDuration = eventEndTime - eventStartTime;\n" +
        "        var timeIntoFinalLoop = totalEventDuration % loopDuration;\n" +
        "        var timeRemainingInLoop = loopDuration - timeIntoFinalLoop;\n" +
        "\n" +
        "        if (timeRemainingInLoop < cutDuration || timeRemainingInLoop > cutDuration2) {\n" +
        "            finalOpacity = 0; // 最后一个循环距离结尾过短或过长直接放弃\n" +
        "        } else {\n" +
        "            if (time < eventEndTime + timeRemainingInLoop) {\n" +
        "                finalOpacity = idealOpacity; // 剩余时间足够，继续播放完这一段\n" +
        "            } else {\n" +
        "                finalOpacity = 0; // 播放完毕，关闭\n" +
        "            }\n" +
        "        }\n" +
        "    }\n" +
        "}\n" +
        "finalOpacity;";

    var midMouthExpression = "var threshold = 2.0; // 阈值\n" +
        "var onDuration = 0.1; // 大嘴时长\n" +
        "var halfDuration = 0.06; // 中嘴时长\n" +
        "var offDuration = 0.18; // 闭嘴时长\n" +
        "var cutDuration = onDuration; // 收尾动画的截止时长参数1\n" +
        "var cutDuration2 = halfDuration // 收尾动画的截止时长参数1\n" +
        "\n" +
        "var frame = thisComp.frameDuration;\n" +
        "var amplitude = thisComp.layer(\"音频振幅\").effect(\"两个通道\")(\"滑块\");\n" +
        "var loopDuration = onDuration + halfDuration + offDuration + halfDuration;\n" +
        "\n" +
        "var eventStartTime = -1;\n" +
        "var eventEndTime = -1;\n" +
        "var inEvent = (amplitude.valueAtTime(time) > threshold);\n" +
        "\n" +
        "if (inEvent) {\n" +
        "    var t = time;\n" +
        "    while (t >= 0) { if (amplitude.valueAtTime(t) > threshold) { t -= frame; } else { break; } }\n" +
        "    eventStartTime = t + frame;\n" +
        "} else {\n" +
        "    var t = time - frame;\n" +
        "    var foundEvent = false;\n" +
        "    while (t >= 0) { if (amplitude.valueAtTime(t) > threshold) { eventEndTime = t; foundEvent = true; break; } t -= frame; }\n" +
        "    if (foundEvent) {\n" +
        "        var t2 = eventEndTime;\n" +
        "        while (t2 >= 0) { if (amplitude.valueAtTime(t2) > threshold) { t2 -= frame; } else { break; } }\n" +
        "        eventStartTime = t2 + frame;\n" +
        "    }\n" +
        "}\n" +
        "\n" +
        "var finalOpacity = 0;\n" +
        "if (eventStartTime !== -1) {\n" +
        "    var blinkingClock = time - eventStartTime;\n" +
        "    var cycle = blinkingClock % loopDuration;\n" +
        "    \n" +
        "    var isHalfMouthTime = (cycle >= onDuration && cycle < onDuration + halfDuration) || (cycle >= onDuration + halfDuration + offDuration && cycle < loopDuration);\n" +
        "    var idealOpacity = isHalfMouthTime ? 100 : 0;\n" +
        "\n" +
        "    if (inEvent) {\n" +
        "        finalOpacity = idealOpacity;\n" +
        "    } else { // 声音停止，进入收尾判断逻辑\n" +
        "        var totalEventDuration = eventEndTime - eventStartTime;\n" +
        "        var timeIntoFinalLoop = totalEventDuration % loopDuration;\n" +
        "        var timeRemainingInLoop = loopDuration - timeIntoFinalLoop;\n" +
        "\n" +
        "        if (timeRemainingInLoop < cutDuration || timeRemainingInLoop > cutDuration2) {\n" +
        "            finalOpacity = 0;\n" +
        "        } else {\n" +
        "            if (time < eventEndTime + timeRemainingInLoop) {\n" +
        "                finalOpacity = idealOpacity;\n" +
        "            } else {\n" +
        "                finalOpacity = 0;\n" +
        "            }\n" +
        "        }\n" +
        "    }\n" +
        "}\n" +
        "finalOpacity;";

    var eyeExpression = "var flickerDuration = 0.2; // 不透明度为0（闪烁）的持续时间（秒）\n" +
        "var minInterval = 6.0;     // 两次闪烁之间的最小间隔时间（秒）\n" +
        "var maxInterval = 10.0;    // 两次闪烁之间的最大间隔时间（秒）\n" +
        "// -----------------\n" +
        "\n" +
        "var t = 0; // 这是一个时间指针，从0秒开始计算\n" +
        "var opacityValue = 100; // 默认不透明度为100\n" +
        "\n" +
        "// 启动一个循环，从时间线开头开始，一步步地计算出所有闪烁事件的发生时间点\n" +
        "// 直到计算的时间点超过了当前播放头的时间\n" +
        "while (t <= time) {\n" +
        "\n" +
        "    // 这是最关键的一步：\n" +
        "    // 我们使用上一个事件的结束时间点(t)作为“随机种子”。\n" +
        "    // 只要种子不变，生成的随机数就永远是同一个值。\n" +
        "    // 这保证了两次闪烁之间的间隔时间是固定的，不会在播放时变来变去。\n" +
        "    seedRandom(t, true);\n" +
        "    \n" +
        "    // 根据设定的范围，生成一个随机的间隔时间\n" +
        "    var randomInterval = random(minInterval, maxInterval);\n" +
        "    \n" +
        "    // 计算出下一次闪烁的“开始时间”和“结束时间”\n" +
        "    var flickerStartTime = t + randomInterval;\n" +
        "    var flickerEndTime = flickerStartTime + flickerDuration;\n" +
        "    \n" +
        "    // 判断一下，当前播放头的时间（time）是否正好落在了我们算出的这个闪烁区间内\n" +
        "    if (time >= flickerStartTime && time < flickerEndTime) {\n" +
        "        opacityValue = 0; // 如果是，那么这一帧的不透明度就应该是0\n" +
        "        break; // 既然已经找到了，就没必要再继续往后计算了，跳出循环\n" +
        "    }\n" +
        "    \n" +
        "    // 如果当前时间不在这次闪烁的区间内，\n" +
        "    // 我们就把时间指针t“跳”到这次闪烁结束的时刻，准备计算下下一次闪烁\n" +
        "    t = flickerEndTime;\n" +
        "}\n" +
        "\n" +
        "// 将最终计算出的不透明度值输出\n" +
        "opacityValue;";

    // --- Helper Function: srtTimeToSeconds ---
    function srtTimeToSeconds(timeString) {
        var parts = timeString.replace(',', '.').split(':');
        var hours = parseFloat(parts[0]);
        var minutes = parseFloat(parts[1]);
        var seconds = parseFloat(parts[2]);
        return hours * 3600 + minutes * 60 + seconds;
    }

    // --- Main Logic ---
    var comp = app.project.activeItem;
    if (!comp || !(comp instanceof CompItem)) {
        alert("请先选择或打开一个合成 (Composition)！");
        return;
    }

    var pngFolder = Folder.selectDialog("请选择包含 PNG 图片的文件夹");
    if (pngFolder === null) { return; }

    var wavFolder = Folder.selectDialog("请选择包含 WAV 文件的文件夹");
    if (wavFolder === null) { return; }

    var srtFile = File.openDialog("请选择一个 .srt 字幕文件", "*.srt", false);
    if (!srtFile) { return; }

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

    if (subtitles.length === 0) { alert("未能从文件中解析出任何字幕条目。"); return; }

    app.beginUndoGroup("导入SRT、WAV和PNG并自动排序+表达式 (V4.3 多|符号处理+翻转)");

    var compCenter = [comp.width / 2, comp.height / 2];
    var audioLayers = [], textLayers = [], imageLayers = [];
    var flipRanges = []; // --- (新) 用于存储需要翻转的时间段

    for (var i = 0; i < subtitles.length; i++) {
        var sub = subtitles[i];
        var rawText = sub.text;
        var pngNameToImport = null;
        var textColor = [0, 0, 0];
        
        // --- (新) 修改了对 | 的解析逻辑 ---
        var parts = rawText.split('|');
        var textContent = parts[0].replace(/^\s+|\s+$/g, ''); // 真正的字幕内容

        if (parts.length > 1) {
            // 第一个 | 之后的内容是图片名
            pngNameToImport = parts[1].replace(/^\s+|\s+$/g, '');
        }
        if (parts.length > 2 && parts[2].replace(/^\s+|\s+$/g, '') === '翻') {
            // 第二个 | 之后如果是 "翻", 则记录这个时间段
            flipRanges.push({ start: sub.startTime, end: sub.endTime });
        }
        // --- (新) 解析逻辑结束 ---

        if (textContent.toLowerCase().indexOf("r:") === 0) {
            textColor = [1, 0, 0]; // Red color
            textContent = textContent.substring(2);
        }
        if (textContent.toLowerCase().indexOf("j:") === 0) {
            textContent = textContent.substring(2);
        }
        textContent = textContent.replace(/^\s+|\s+$/g, '');

        var formattedId = ("0000" + sub.id).slice(-4);
        var foundWavFiles = wavFolder.getFiles(formattedId + "*.wav");
        var audioLayer = null;

        var layerInPoint = sub.startTime;
        var layerOutPoint = sub.endTime;

        if (foundWavFiles.length > 0) {
            try {
                var importedFootage = app.project.importFile(new ImportOptions(foundWavFiles[0]));
                audioLayer = comp.layers.add(importedFootage);
                audioLayer.name = "Audio " + sub.id;
                audioLayer.startTime = layerInPoint;
                audioLayers.push(audioLayer);
            } catch (e) {
                alert("导入 WAV '" + foundWavFiles[0].name + "' 时出错: " + e.toString());
            }
        } else {
            alert("警告: 未找到与字幕 ID " + sub.id + " 对应的 WAV 文件。文本和图片仍将创建。");
        }

        var textLayer = comp.layers.addText(textContent);
        textLayer.name = "Subtitle " + sub.id;
        textLayer.inPoint = layerInPoint;
        textLayer.outPoint = layerOutPoint;
        textLayers.push(textLayer);

        var textProp = textLayer.property("Source Text");
        var textDocument = textProp.value;
        try { textDocument.font = FONT_NAME; } catch (fontError) { alert("字体 '" + FONT_NAME + "' 设置失败: " + fontError.toString()); }
        textDocument.fontSize = TEXT_FONT_SIZE;
        textDocument.justification = ParagraphJustification.CENTER_JUSTIFY;
        textDocument.fillColor = textColor;
        textDocument.leading = 80;
        textDocument.tracking = -50;
        textDocument.applyStroke = true;
        textDocument.strokeWidth = 2;
        textDocument.strokeOverFill = true;
        textProp.setValue(textDocument);

        var sourceRect = textLayer.sourceRectAtTime(layerInPoint, false);
        textLayer.property("Transform").property("Anchor Point").setValue([sourceRect.left + sourceRect.width / 2, sourceRect.top + sourceRect.height / 2]);
        textLayer.property("Transform").property("Position").setValue(compCenter);
        textLayer.property("Transform").property("Scale").expression = "var animDuration = " + ANIMATION_DURATION.toFixed(3) + "; var overdriveScale = " + APPEAR_OVERDRIVE_SCALE.toFixed(3) + "; var fullScale = [100, 100]; var noScale = [0, 0]; var t = time - thisLayer.inPoint; var layerDuration = thisLayer.outPoint - thisLayer.inPoint; if (t >= 0 && t < animDuration) { var appearMidTime = animDuration * 0.7; if (t < appearMidTime) { ease(t, 0, appearMidTime, noScale, [overdriveScale, overdriveScale]); } else { ease(t, appearMidTime, animDuration, [overdriveScale, overdriveScale], fullScale); } } else if (t > layerDuration - animDuration && t <= layerDuration + 0.0001) { var timeIntoDisappear = t - (layerDuration - animDuration); ease(timeIntoDisappear, 0, animDuration, fullScale, noScale); } else if (t >= animDuration && t <= layerDuration - animDuration) { fullScale; } else { if (layerDuration < animDuration) noScale; else if (t > animDuration && layerDuration < 2 * animDuration) fullScale; else noScale; }";

        if (pngNameToImport) {
            var pngFile = new File(pngFolder.fsName + "/" + pngNameToImport + ".png");
            if (pngFile.exists) {
                try {
                    var pngLayer = comp.layers.add(app.project.importFile(new ImportOptions(pngFile)));
                    pngLayer.name = pngNameToImport + " - " + sub.id;
                    pngLayer.inPoint = layerInPoint;
                    pngLayer.outPoint = layerOutPoint;
                    pngLayer.property("Transform").property("Position").setValue([1654, 1006]);
                    // --- 注意: 这里先设置一个初始值，后续会被翻转表达式覆盖 ---
                    pngLayer.property("Transform").property("Scale").setValue([57.1165, 57.1165]);
                    imageLayers.push(pngLayer);
                } catch (e) { alert("导入 PNG '" + pngFile.name + "' 时出错: " + e.toString()); }
            } else { alert("警告: 未找到图片 '" + pngNameToImport + ".png'。"); }
        }
    }

    var baseLayer = null, midMouthLayer = null, bigMouthLayer = null, eyeLayer = null;
    var staticImageNames = ["base.png", "眼.png", "中嘴.png", "大嘴.png"];

    for (var j = 0; j < staticImageNames.length; j++) {
        var imageName = staticImageNames[j];
        var imageFile = new File(pngFolder.fsName + "/" + imageName);
        if (imageFile.exists) {
            try {
                var layer = comp.layers.add(app.project.importFile(new ImportOptions(imageFile)));
                layer.name = imageName.split('.')[0];
                layer.inPoint = 0;
                layer.outPoint = comp.duration;
                layer.property("Transform").property("Position").setValue([1654, 1006]);
                 // --- 注意: 这里同样先设置一个初始值 ---
                layer.property("Transform").property("Scale").setValue([57.1165, 57.1165]);

                if (imageName === "base.png") baseLayer = layer;
                else if (imageName === "眼.png") eyeLayer = layer;
                else if (imageName === "中嘴.png") midMouthLayer = layer;
                else if (imageName === "大嘴.png") bigMouthLayer = layer;
            } catch (e) { alert("导入静态图片 '" + imageName + "' 时出错: " + e.toString()); }
        } else { alert("警告: 静态图片 '" + imageName + "' 未找到。"); }
    }
    
    // --- (新) 为需要翻转的图层统一应用缩放表达式 ---
    if (flipRanges.length > 0) {
        var scaleConditions = [];
        for (var k = 0; k < flipRanges.length; k++) {
            scaleConditions.push("(time >= " + flipRanges[k].start.toFixed(5) + " && time < " + flipRanges[k].end.toFixed(5) + ")");
        }
        var scaleExpression = "var isFlipTime = " + scaleConditions.join(" || ") + ";\n" +
                              "var baseScale = [57.1165, 57.1165];\n" +
                              "if (isFlipTime) { [-baseScale[0], baseScale[1]]; } else { baseScale; }";
        
        // 应用到静态图层
        if (baseLayer) { baseLayer.property("Transform").property("Scale").expression = scaleExpression; }
        if (eyeLayer) { eyeLayer.property("Transform").property("Scale").expression = scaleExpression; }
        if (midMouthLayer) { midMouthLayer.property("Transform").property("Scale").expression = scaleExpression; }
        if (bigMouthLayer) { bigMouthLayer.property("Transform").property("Scale").expression = scaleExpression; }
        
        // 应用到所有特殊图片图层
        for (var k = 0; k < imageLayers.length; k++) {
            imageLayers[k].property("Transform").property("Scale").expression = scaleExpression;
        }
    }

    if (baseLayer && imageLayers.length > 0) {
        var expressionConditions = [];
        for (var k = 0; k < imageLayers.length; k++) {
            var layerName = imageLayers[k].name.replace(/'/g, "\\'");
            expressionConditions.push("(time >= thisComp.layer('" + layerName + "').inPoint && time < thisComp.layer('" + layerName + "').outPoint)");
        }
        var baseOpacityExpression = expressionConditions.join(" || ") + " ? 0 : 100;";
        baseLayer.property("Transform").property("Opacity").expression = baseOpacityExpression;
    }

    if (bigMouthLayer) { bigMouthLayer.property("Transform").property("Opacity").expression = bigMouthExpression; }
    if (midMouthLayer) { midMouthLayer.property("Transform").property("Opacity").expression = midMouthExpression; }
    if (eyeLayer) { eyeLayer.property("Transform").property("Opacity").expression = eyeExpression; }
    
    // 重新排序图层
    for (var k = 0; k < audioLayers.length; k++) { audioLayers[k].moveToEnd(); }
    for (var k = 0; k < textLayers.length; k++) { textLayers[k].moveToBeginning(); }
    if (baseLayer) { baseLayer.moveToBeginning(); }
    if (eyeLayer) { eyeLayer.moveToBeginning(); }
    for (var k = 0; k < imageLayers.length; k++) { imageLayers[k].moveToBeginning(); }
    if (midMouthLayer) { midMouthLayer.moveToBeginning(); }
    if (bigMouthLayer) { bigMouthLayer.moveToBeginning(); }

    app.endUndoGroup();
    alert("脚本执行完毕！\n已创建图层并完成排序，所有图层均基于SRT时间戳定位，同时为嘴型、眼睛及需要翻转的图层添加了动画表达式。");

})();