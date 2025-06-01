import keyboard
import os
import random
import pygame.mixer

# 指定存放音频文件的文件夹（请修改为你的音频文件夹路径）
AUDIO_FOLDER = r"E:\\mande\\0_important\\0_script\\APEXVOICE"

# 初始化 pygame 音频播放器
pygame.mixer.init()

# 存储按键对应的音频文件（仅限 1-9）
audio_files = {str(i): [] for i in range(1, 10)}

# 读取文件夹中的音频文件（文件名格式：1_xxx.mp3, 2_xxx.mp3...）
for file in os.listdir(AUDIO_FOLDER):
    if file.endswith((".mp3", ".wav")):
        first_char = file[0]  # 获取文件名的第一个字符
        if first_char.isdigit() and first_char in audio_files:
            audio_files[first_char].append(os.path.join(AUDIO_FOLDER, file))

# 播放音频的函数
def play_audio(num_key):
    if num_key in audio_files and audio_files[num_key]:
        audio_file = random.choice(audio_files[num_key])  # 随机选择一个文件播放
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        print(f"正在播放: {audio_file}")

# 小键盘数字键的 scan_code
numpad_scan_codes = {
    '1': 79,
    '2': 80,
    '3': 81,
    '4': 75,
    '5': 76,
    '6': 77,
    '7': 71,
    '8': 72,
    '9': 73
}

def on_press(event):
    if event.scan_code in numpad_scan_codes.values():
        num_key = [k for k, v in numpad_scan_codes.items() if v == event.scan_code][0]
        play_audio(num_key)
    elif event.scan_code == 53:  # '/' 键的 scan_code
        keyboard.unhook_all()
        print("音频播放程序已退出")

keyboard.on_press(on_press)

print("音频播放程序已启动，按小键盘数字 (1-9) 播放对应的音频。按 '/' 退出。")
keyboard.wait()