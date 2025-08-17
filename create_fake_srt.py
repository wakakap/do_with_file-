import datetime

def format_time(seconds):
    """将秒数格式化为 SRT 时间戳格式 HH:MM:SS,ms"""
    delta = datetime.timedelta(seconds=seconds)
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = delta.microseconds // 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def create_srt_from_text(input_file='input.txt', output_file='output.srt', duration_seconds=3):
    """
    读取文本文件，为每一行创建一个持续指定秒数的 SRT 字幕文件。

    :param input_file: 输入的文本文件名。
    :param output_file: 输出的 SRT 文件名。
    :param duration_seconds: 每条字幕的持续时间（秒）。
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f_in:
            lines = f_in.readlines()
    except FileNotFoundError:
        print(f"错误：找不到输入文件 '{input_file}'。请确保文件存在于正确的路径。")
        return

    with open(output_file, 'w', encoding='utf-8') as f_out:
        start_time = 0
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:  # 跳过空行
                continue

            end_time = start_time + duration_seconds

            f_out.write(str(i + 1) + '\n')
            f_out.write(f"{format_time(start_time)} --> {format_time(end_time)}\n")
            f_out.write(line + '\n\n')

            start_time = end_time

    print(f"成功！已将 '{input_file}' 中的内容转换为 SRT 格式，并保存为 '{output_file}'。")
    print(f"共处理了 {len(lines)} 行文本。")

if __name__ == '__main__':
    # --- 可在此处自定义参数 ---
    input_filename = 'E:/抽吧唧/naruto/o.srt'
    output_filename = 'E:/抽吧唧/naruto/1.srt'
    subtitle_duration = 3  # 每条字幕的持续时间（秒）
    # -------------------------

    create_srt_from_text(input_filename, output_filename, subtitle_duration)