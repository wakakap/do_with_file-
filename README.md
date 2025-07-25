+ 检索：
  + 二次元图片检索：https://ascii2d.net/
  + 图片来自哪部动画：https://trace.moe/
  + 查Latex符号：https://detexify.kirelabs.org/
  + 查Unicode：https://shapecatcher.com/
  + 查书籍：https://search.worldcat.org/
+ API检索: 
  + GOOGLE SEARCH: https://serpapi.com/
  + BANGUMI: https://bangumi.github.io/api/
  + DMM: https://pypi.org/project/dmm-search3/ https://affiliate.dmm.com/api/guide/
+ 文件处理：
  + 文件转换：https://www.aconvert.com/
  + 文件转换：https://pandoc.org/ `pandoc article.tex --bibliography=reference.bib --citeproc -o output.docx`
  + pdf复制清除空格：https://laorange.github.io/paper-assistant/
+ 视频处理：
  + ffmpeg: 重点参数为`-crf 15`，越低质量越高，一般`21`可接受且体积小。ffmpeg的合并片段效果非常差，出现音画偏移，暂未解决办法，还是导入Pr处理。
    + 编码：`ffmpeg -i "1.mov" -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 128k -y "2.mp4"`
    + 截取：`ffmpeg -ss 0:00:00 -i "sum.mp4" -t 208 -codec copy -y "sum2.mp4"`
    + 截取+编码：`ffmpeg -ss 00:01:28 -i "1.webm" -t 20 -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 128k -y "2.mp4"`
    + 加帧（最小蠕动感）：`ffmpeg -i "video.mp4" -vf "minterpolate=fps=60:mi_mode=blend:scd=1" "video60fps.mp4"`
    + 加字幕（必须编码）：`ffmpeg -i "video60fps.mp4" -vf "ass=jp_ch_reconstructed.ass" -c:a aac -b:a 128k "5.mp4"`
+ 图片处理：
  + 放大：Upscayl
+ 下载：
  + yt-dlp: 适用于youtube,twitch,bilibili，不适用于twitter
    + `yt-dlp -F URL`
    + `yt-dlp -f 30232 URL`
    + `yt-dlp "https://www.youtube.com/watch?v=xxx"`
    + `yt-dlp "https://www.youtube.com/watch?v=xxx"  -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4"`
    + `yt-dlp "https://www.twitch.tv/videos/xxxx" -o "E:\xxxx\xxxx.mp4" -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4" --download-sections "*00:13:00-07:54:10"`
    + pip install getjump  https://pypi.org/project/getjump/
      + `jget https://shonenjumpplus.com/episode/xxxx` 适用于comic-action.com comic-days.com comic-earthstar.com comic-gardo.com comic-ogyaaa.com comic-seasons.com comic-trail.com comic-zenon.com comicborder.com feelweb.jp kuragebunch.com magcomi.com ourfeel.jp pocket.shonenmagazine.com shonenjumpplus.com www.sunday-webry.com tonarinoyj.jp viewer.heros-web.com
    + pip install cowado https://pypi.org/project/cowado/ 
      + `cowado url` 适用于 comic-walker.com
  + BT:
    + 设置：VPN:KILL SWITCH
    + qbittorent：高级-网络接口-VPN, 隐私-强制加密，匿名模式，速度限制。上传速度不能太低，否则没下载速度。
      + ~~盗版站：https://nyaa.si~~  ~~https://sukebei.nyaa.si~~ ~~e-hentai.org~~
      + ~~压制组：https://vcb-s.com/ https://nyaa.si/user/VCB-Studio~~
  + PT: 
    + ~~之前用西北工业大学的蒲公英，现在基本很难了~~
+ AI
  + AI对比（免费用）：https://lmarena.ai/
  + AI训练语音：https://github.com/RVC-Boss/GPT-SoVITS
  + AI音乐：https://www.suno.ai/  
  + AI作画：https://github.com/AUTOMATIC1111/stable-diffusion-webui
  + OpenAI：https://chat.openai.com/
  + Grok: https://x.ai/grok
  + Gemini: 成了pro很爽 https://gemini.google.com/
+ 硬件
  + 硬盘检测：https://crystalmark.info/ja/download/
+ 系统
  + 定时1小时后关机 `shutdown /s /t 3600`
  + windows隐私关闭：https://github.com/builtbybel/privatezilla
  + 安装系统：http://rufus.ie/
+ 软件
  + 常用
    + 播放器：https://potplayer.daum.net/
    + 压缩软件：WinRAR
    + 编辑软件：VScode
    + pdf软件：福昕
    + 聊天/文件传送：telegram
    + 直播/录制：OBS https://obsproject.com/
    + 音频通道控制：VB-CABLE https://vb-audio.com/Cable/
    + 加载安装包：~~deamon tool lite https://www.daemon-tools.cc/products/dtLite ~~ 现在有垃圾捆绑了
      + WinCDEmu https://wincdemu.sysprogs.org/download/
  + 学术
    + 流程图: https://github.com/jgraph
    + Zotero：搭配网盘使用，自制免费同步，注意安装路径的设置
    + 坚果云网盘：阶段性给予存储容量
  + 创作
    + VOICEVOX: 文字转语音，免费商用 https://voicevox.hiroshiba.jp/ 可打开软件时调用api开发应用
    + Adobe: AE, Pr, ...
    + ultimatevocalremover：分离视频人声的AI开源工具，效果惊人

# 常用指令

```bash
shutdown /s /t 3600
yt-dlp -F URL
yt-dlp -f 30232 URL
yt-dlp "https://www.youtube.com/watch?v=xxx"
yt-dlp "https://www.youtube.com/watch?v=xxx"  -f "137+233-0"
yt-dlp "https://www.youtube.com/watch?v=xxx"  -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4"
yt-dlp "https://www.twitch.tv/videos/xxxx" -o "E:\xxxx\xxxx.mp4" -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4" --download-sections "*00:13:00-07:54:10"
ffmpeg -ss 0:30:00 -i "output_1.mp4" -t 600 -codec copy -y "output_1.4.mp4"
ffmpeg -ss 00:01:28 -i "【ゼンゼロ】モエチャッカファイア ⧸  エレン・ジョー（CV：若山詩音）cover [rTqYRWcA-Yw].webm" -t 20 -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 128k -y "モエチャッカファイア.mp4"
ffmpeg -i "llll.mov" -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 128k -y "llll.mp4"
ffmpeg -ss 00:03:30 -i "フレデリック「オドループ」Music Video ｜ Frederic ＂oddloop＂ [PCp2iXA1uLE].webm" -t 40 -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 128k -y "bgm.mp4"
ffmpeg -i "video.mp4" -vf "minterpolate=fps=60:mi_mode=blend:scd=1" "video60fps.mp4"
ffmpeg -i "video60fps_1.mp4" -vf "ass=20250709_so45124910_comments_CH_extend.ass" -c:a copy final.mp4

pip install 
pip uninstall 
pip cache purge
pyinstaller --noconfirm -w --onefile --icon=icon.ico main.py
```