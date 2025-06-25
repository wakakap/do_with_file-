# 常用指令

```bash
shutdown /s /t 3600
yt-dlp -F URL
yt-dlp -f 30232 URL
yt-dlp "https://www.youtube.com/watch?v=xxx"
yt-dlp "https://www.youtube.com/watch?v=xxx"  -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4"
yt-dlp "https://www.twitch.tv/videos/xxxx" -o "E:\xxxx\xxxx.mp4" -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4" --download-sections "*00:13:00-07:54:10"
ffmpeg -ss 3:01:25 -i "E:\xxx\xxx.mp4" -t 230 -codec copy -y "E:\xxx\xxx.mp4"
ffmpeg -ss 00:01:28 -i "ika.webm" -t 20 -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 128k -y "ika.mp4"
ffmpeg -ss 00:03:30 -i "フレデリック「オドループ」Music Video ｜ Frederic ＂oddloop＂ [PCp2iXA1uLE].webm" -t 40 -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 128k -y "bgm.mp4"

pip install 
pip uninstall 
pyinstaller --noconfirm -w --onefile --icon=icon.ico main.py
```