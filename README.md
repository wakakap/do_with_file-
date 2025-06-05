# 常用指令

```bash
shutdown /s /t 3600
yt-dlp "https://www.youtube.com/watch?v=xxx"
yt-dlp "https://www.youtube.com/watch?v=xxx"  -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4"
yt-dlp "https://www.twitch.tv/videos/xxxx" -o "E:\xxxx\xxxx.mp4" -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4" --download-sections "*00:13:00-07:54:10"
ffmpeg -ss 3:01:25 -i "E:\xxx\xxx.mp4" -t 230 -codec copy -y "E:\xxx\xxx.mp4"
pip install 
pip uninstall 
pyinstaller --noconfirm -w --onefile --icon=icon.ico main.py
```