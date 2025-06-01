# 界面小软件 边听音乐边按键盘，记录成srt文件
# 选择开始时间和激活的按键 i,j,k 的格式
import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk
import keyboard
from datetime import datetime

key_events = []
recording = False
start_time = None
key_active = {}
initial_seconds = 0  # 新增变量来存储用户输入的初始秒数

def ask_for_keys():
    """要求用户输入要跟踪的按键，并更新key_active字典"""
    global key_active, initial_seconds
    root = tk.Tk()
    root.withdraw() # 隐藏额外的Tk窗口

    # 简单对话框要求输入初始秒数
    initial_seconds_str = simpledialog.askstring("Input", "Enter initial seconds:")
    try:
        initial_seconds = int(initial_seconds_str)
    except ValueError:
        initial_seconds = 0  # 如果输入无效，设置为0

    # 简单对话框要求输入
    keys_string = simpledialog.askstring("Input", "Enter keys to record separated by commas (e.g., a,b,c):")
    # 处理输入和更新key_active
    if keys_string:
        keys_list = keys_string.split(',')
        for key in keys_list:
            key_trimmed = key.strip() # 去掉空格
            key_active[key_trimmed] = False # 初始化为未激活
    root.destroy()

def on_key_event(event):
    global key_events, start_time, initial_seconds  # 使用全局变量initial_seconds
    if not recording or event.name not in key_active:
        return
    timestamp = (datetime.now() - start_time).total_seconds() + initial_seconds  # 加上初始秒数
    if event.event_type == 'down' and not key_active[event.name]:
        key_active[event.name] = True
        key_events.append((event.name, 'down', timestamp))
        print(f"Captured event: {event.name}, down, at {timestamp} seconds")
    elif event.event_type == 'up' and key_active[event.name]:
        key_active[event.name] = False
        key_events.append((event.name, 'up', timestamp))
        print(f"Captured event: {event.name}, up, at {timestamp} seconds")

def start_recording():
    global recording, start_time, key_events
    recording = True
    start_time = datetime.now()
    key_events = []
    print("Recording started.")

def stop_recording():
    global recording
    recording = False
    print("Recording stopped.")
    save_to_srt()

def save_to_srt():
    with open('output.srt', 'w', encoding='utf-8') as file:
        for idx, (key, event_type, timestamp) in enumerate(key_events, start=1):
            if event_type == 'down':
                start = timestamp
                for next_idx, next_event in enumerate(key_events[idx:], start=1):
                    if next_event[0] == key and next_event[1] == 'up':
                        end = next_event[2]
                        break
                
                start_srt = seconds_to_srt_time(start)
                end_srt = seconds_to_srt_time(end)
                
                file.write(f"{idx}\n{start_srt} --> {end_srt}\n{key}\n\n")

def seconds_to_srt_time(seconds):
    """将秒转换为SRT时间格式HH:MM:SS,MMM"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = (seconds - int(seconds)) * 1000
    return "{:02}:{:02}:{:02},{:03}".format(int(hours), int(minutes), int(seconds), int(milliseconds))

def main():
    ask_for_keys()  # 在程序开始时要求用户输入初始秒数和按键
    root = tk.Tk()
    root.title("Keyboard Event Recorder")

    start_button = ttk.Button(root, text="Start", command=start_recording)
    start_button.pack(side=tk.LEFT, padx=(20, 10), pady=20)

    stop_button = ttk.Button(root, text="Stop", command=stop_recording)
    stop_button.pack(side=tk.RIGHT, padx=(10, 20), pady=20)

    keyboard.hook(on_key_event)

    root.mainloop()

if __name__ == "__main__":
    main()
