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
    根据WAV文件时长修改SRT文件的时间戳。
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

    current_time_ms = 0  # 初始时间为0毫秒

    for sub in subs:
        wav_index = sub.index  # SRT字幕的序号
        wav_path = wav_files.get(wav_index)

        if wav_path:
            duration = get_wav_duration(wav_path)
            if duration is not None:
                # 设置开始时间
                sub.start.milliseconds = current_time_ms % 1000
                sub.start.seconds = (current_time_ms // 1000) % 60
                sub.start.minutes = (current_time_ms // (1000 * 60)) % 60
                sub.start.hours = (current_time_ms // (1000 * 60 * 60))

                # 更新当前时间为结束时间
                end_time_ms = current_time_ms + int(duration * 1000)
                sub.end.milliseconds = end_time_ms % 1000
                sub.end.seconds = (end_time_ms // 1000) % 60
                sub.end.minutes = (end_time_ms // (1000 * 60)) % 60
                sub.end.hours = (end_time_ms // (1000 * 60 * 60))

                # 更新下一个字幕的开始时间（当前字幕结束时间 + 0.1秒间隔）
                current_time_ms = end_time_ms + 100 # 0.1秒间隔
            else:
                print(f"Could not get duration for WAV file corresponding to SRT index {wav_index}. Skipping time update for this subtitle.")
        else:
            print(f"No WAV file found for SRT index {wav_index}. Skipping time update for this subtitle.")
            # 如果没有对应的WAV文件，为了保持时间戳的连续性，
            # 可以选择给一个默认的持续时间或者直接跳过更新
            # 这里我们选择不更新时间，但会打印警告

    output_file_path = os.path.join(os.path.dirname(srt_file_path), "revised.srt")
    try:
        subs.save(output_file_path, encoding='utf-8')
        print(f"Revised SRT file saved to: {output_file_path}")
    except Exception as e:
        print(f"Error saving revised SRT file: {e}")

if __name__ == "__main__":
        # --- 请在这里修改你的SRT文件和WAV文件夹路径 ---
        my_srt_file = "E:\\抽吧唧\\もりもり\\反省会.srt"
        my_wav_folder = "E:\\抽吧唧\\もりもり\\sub"
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