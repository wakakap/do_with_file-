import os
import pysrt
import wave
import argparse

def get_wav_duration(file_path):
    """
    获取WAV文件的时长（秒）。
    """
    try:
        with wave.open(file_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            return duration
    except Exception as e:
        print(f"Error reading WAV file {file_path}: {e}")
        return None

def revise_srt(srt_file_path, wav_folder_path):
    """
    根据WAV文件时长修改SRT文件的结束时间戳。
    开始时间将保持不变。
    """
    try:
        subs = pysrt.open(srt_file_path, encoding='utf-8')
    except Exception as e:
        print(f"Error opening SRT file {srt_file_path}: {e}")
        return

    wav_files = {}
    for filename in os.listdir(wav_folder_path):
        if filename.lower().endswith('.wav'):
            try:
                # 获取文件名前4位作为序号
                index_str = filename[:4]
                index = int(index_str)
                wav_files[index] = os.path.join(wav_folder_path, filename)
            except ValueError:
                print(f"Skipping malformed WAV filename: {filename} (index not found)")
                continue

    for sub in subs:
        wav_index = sub.index  # SRT字幕的序号
        wav_path = wav_files.get(wav_index)

        if wav_path:
            duration_sec = get_wav_duration(wav_path)
            if duration_sec is not None:
                # --- 新逻辑 ---
                # 保留原始的开始时间
                start_time = sub.start
                
                # 计算结束时间
                # 将原始开始时间转换为总毫秒数
                start_time_ms = (start_time.hours * 3600 + start_time.minutes * 60 + start_time.seconds) * 1000 + start_time.milliseconds
                
                # 计算结束时间的总毫秒数
                duration_ms = int(duration_sec * 1000)
                end_time_ms = start_time_ms + duration_ms
                
                # 更新字幕的结束时间
                sub.end.milliseconds = end_time_ms % 1000
                sub.end.seconds = (end_time_ms // 1000) % 60
                sub.end.minutes = (end_time_ms // (1000 * 60)) % 60
                sub.end.hours = (end_time_ms // (1000 * 60 * 60))
                
            else:
                print(f"Could not get duration for WAV file corresponding to SRT index {wav_index}. Skipping time update for this subtitle.")
        else:
            print(f"No WAV file found for SRT index {wav_index}. Skipping time update for this subtitle.")

    # 构建输出文件名，在原文件名后加上"_revised"
    base, ext = os.path.splitext(srt_file_path)
    output_file_path = f"{base}_revised{ext}"
    
    try:
        subs.save(output_file_path, encoding='utf-8')
        print(f"Revised SRT file saved to: {output_file_path}")
    except Exception as e:
        print(f"Error saving revised SRT file: {e}")

if __name__ == "__main__":
        # --- 请在这里修改你的SRT文件和WAV文件夹路径 ---
        my_srt_file = "E:\\抽吧唧\\看章鱼反应\\4_reordered.srt"
        my_wav_folder = "E:\\抽吧唧\\看章鱼反应\\sub"
        # -----------------------------------------------

        # 检查文件和文件夹是否存在
        if not os.path.exists(my_srt_file):
            print(f"错误：SRT文件 '{my_srt_file}' 不存在。")
        elif not os.path.isfile(my_srt_file):
            print(f"错误：'{my_srt_file}' 不是一个文件。")
        elif not os.path.exists(my_wav_folder):
            print(f"错误：WAV文件夹 '{my_wav_folder}' 不存在。")
        elif not os.path.isdir(my_wav_folder):
            print(f"错误：'{my_wav_folder}' 不是一个文件夹。")
        else:
            revise_srt(my_srt_file, my_wav_folder)