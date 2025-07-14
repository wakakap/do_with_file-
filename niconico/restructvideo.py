import os
import subprocess
import logging

# --- 配置日志记录 ---
# 配置日志记录器，用于在控制台输出脚本的运行状态和潜在错误。
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def hms_to_seconds(hms_str):
    """将 HH:MM:SS.ss 格式的时间字符串转换为总秒数。"""
    try:
        parts = hms_str.split(':')
        if len(parts) != 3:
            raise ValueError(f"时间格式无效: '{hms_str}'")
        h = int(parts[0])
        m = int(parts[1])
        s_float = float(parts[2])
        return h * 3600 + m * 60 + s_float
    except (ValueError, IndexError) as e:
        raise ValueError(f"无法解析时间 '{hms_str}': {e}")


def seconds_to_hms(seconds):
    """将总秒数转换为 HH:MM:SS.sss 格式的字符串。"""
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def process_video_with_timestamps(
    input_video_path,
    timestamps_file_path,
    output_folder,
    padding_seconds=2.0,
    output_filename_suffix="_PROCESSED"
):
    """
    根据给定的时间范围文件，剪辑并合并视频片段。

    Args:
        input_video_path (str): 输入视频文件的路径。
        timestamps_file_path (str): 包含时间范围的 txt 文件的路径。
        output_folder (str): 输出文件和中间文件的存放目录。
        padding_seconds (float): 在每个时间范围前后增加的秒数。
        output_filename_suffix (str): 添加到输出文件名的后缀。
    """
    # --- 1. 验证输入文件是否存在 ---
    if not os.path.exists(input_video_path):
        logger.error(f"错误: 输入视频文件未找到 {input_video_path}")
        return
    if not os.path.exists(timestamps_file_path):
        logger.error(f"错误: 时间戳文件未找到 {timestamps_file_path}")
        return

    # --- 2. 解析时间戳文件 ---
    time_ranges = []
    try:
        with open(timestamps_file_path, 'r', encoding='utf-8') as f:
            # 移除所有空白字符（包括换行符）并按逗号分割
            content = "".join(f.read().split())
            if not content:
                logger.warning(f"时间戳文件 {timestamps_file_path} 为空。")
                return
            
            # # 格式兼容
            # if content.startswith('', 1)[-1]
            
            ranges_str = content.split(',')
            for i, range_str in enumerate(ranges_str):
                if not range_str.strip():
                    continue
                try:
                    start_hms, end_hms = range_str.split('-')
                    start_sec = hms_to_seconds(start_hms)
                    end_sec = hms_to_seconds(end_hms)
                    
                    adjusted_start = max(0, start_sec - padding_seconds*4)
                    adjusted_end = end_sec + padding_seconds
                    duration = adjusted_end - adjusted_start

                    if duration > 0.01:
                        time_ranges.append({'start': adjusted_start, 'duration': duration})
                    else:
                        logger.warning(f"跳过无效的时间范围 {range_str}，调整后时长过短。")

                except ValueError as e:
                    logger.warning(f"解析第 {i+1} 个时间范围 '{range_str}' 时出错: {e}。已跳过。")
    except Exception as e:
        logger.error(f"读取或解析时间文件 {timestamps_file_path} 时出错: {e}")
        return

    if not time_ranges:
        logger.info("未从文件中解析出有效的时间范围。")
        return

    logger.info(f"成功解析并调整了 {len(time_ranges)} 个时间范围。")

    # --- 3. 准备输出目录和文件名 ---
    os.makedirs(output_folder, exist_ok=True)
    video_name_no_ext = os.path.splitext(os.path.basename(input_video_path))[0]
    video_extension = os.path.splitext(input_video_path)[1] or ".mp4"

    final_output_filename = f"{video_name_no_ext}{output_filename_suffix}{video_extension}"
    final_output_path = os.path.join(output_folder, final_output_filename)

    if os.path.exists(final_output_path):
        logger.info(f"最终合并视频 {final_output_path} 已存在，跳过处理。")
        return

    intermediate_folder_name = f"{video_name_no_ext}_intermediate_parts"
    intermediate_output_folder = os.path.join(output_folder, intermediate_folder_name)
    os.makedirs(intermediate_output_folder, exist_ok=True)
    logger.info(f"中间剪辑文件将保存在: {intermediate_output_folder}")

    # --- 4. 使用 FFmpeg 生成中间剪辑文件 (重新编码) ---
    intermediate_file_paths = []
    for idx, segment in enumerate(time_ranges):
        start_s = segment['start']
        duration_s = segment['duration']
        
        intermediate_file_name = f"part_{idx:04d}{video_extension}"
        intermediate_file_path = os.path.join(intermediate_output_folder, intermediate_file_name)
        
        if os.path.exists(intermediate_file_path):
            logger.info(f"中间文件 {intermediate_file_path} 已存在，将直接使用。")
            intermediate_file_paths.append(intermediate_file_path)
            continue

        logger.info(
            f"正在生成中间文件 {idx+1}/{len(time_ranges)}: "
            f"从 {seconds_to_hms(start_s)} 开始，持续 {duration_s:.2f} 秒"
        )
        
        command_reencode = [
            'ffmpeg', '-ss', str(start_s), '-i', input_video_path,
            '-t', str(duration_s), '-vf', 'setpts=PTS-STARTPTS',
            '-af', 'asetpts=PTS-STARTPTS', '-c:v', 'libx264',
            '-preset', 'medium', '-crf', '19', '-c:a', 'aac',
            '-b:a', '192k', '-loglevel', 'error', '-y', intermediate_file_path
        ]
        
        try:
            subprocess.run(command_reencode, check=True, capture_output=True, text=True, encoding='utf-8')
            logger.info(f"成功生成: {intermediate_file_name}")
            intermediate_file_paths.append(intermediate_file_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"生成 {intermediate_file_name} 时出错 (FFmpeg 返回码: {e.returncode})")
            logger.error(f"FFmpeg 错误输出:\n{e.stderr.strip()}")
            continue

    # --- 5. 合并所有中间文件 ---
    if len(intermediate_file_paths) < len(time_ranges):
        logger.error("部分中间文件生成失败，已中止合并。")
        return
    if not intermediate_file_paths:
        logger.error("未能生成任何有效的中间文件，无法进行合并。")
        return

    concat_list_path = os.path.join(intermediate_output_folder, "concat_list.txt")
    try:
        with open(concat_list_path, 'w', encoding='utf-8') as f:
            for path in intermediate_file_paths:
                f.write(f"file '{os.path.basename(path)}'\n")
        logger.info(f"已创建用于合并的列表文件: {concat_list_path}")
    except IOError as e:
        logger.error(f"创建 concat 列表文件失败: {e}")
        return

    command_concat = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_list_path,
        '-c', 'copy', '-loglevel', 'error', '-y', final_output_path
    ]

    try:
        logger.info(f"正在合并所有片段到: {final_output_path} ...")
        subprocess.run(command_concat, check=True, capture_output=True, text=True, encoding='utf-8')
        logger.info(f"成功生成最终视频: {final_output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"最终合并时出错 (FFmpeg 返回码: {e.returncode})")
        logger.error(f"FFmpeg 错误输出:\n{e.stderr.strip()}")

    logger.info(f"处理完成。中间文件保留在 {intermediate_output_folder} 以供检查。")


if __name__ == '__main__':
    # ==================================================================
    # --- 用户配置区 ---
    # 在运行前，请修改以下变量的值
    # ==================================================================

    # 1. 输入视频的完整路径
    # Windows 示例: "C:\\Users\\YourUser\\Videos\\my_video.mp4"
    # macOS/Linux 示例: "/home/user/videos/my_video.mp4"
    # 请确保路径字符串中的反斜杠 \ 是双写的 \\ 或者使用正斜杠 /
    INPUT_VIDEO = "E:\\抽吧唧\\章鱼p\\3\\3.mp4"

    # 2. 包含时间戳的 txt 文件的完整路径
    TIMESTAMPS_FILE = "niconico/takop/fire_times.txt"

    # 3. 输出文件夹的路径，所有结果都会保存在这里
    OUTPUT_FOLDER = "E:/抽吧唧/章鱼p/3/output_folder"
    
    # 4. (可选) 在每个时间范围前后扩展的秒数
    PADDING_SECONDS = 2.5
    
    # 5. (可选) 添加到输出文件名的后缀
    FILENAME_SUFFIX = "_PROCESSED_CLIPS"

    # ==================================================================
    # --- 执行处理 ---
    # ==================================================================
    process_video_with_timestamps(
        input_video_path=INPUT_VIDEO,
        timestamps_file_path=TIMESTAMPS_FILE,
        output_folder=OUTPUT_FOLDER,
        padding_seconds=PADDING_SECONDS,
        output_filename_suffix=FILENAME_SUFFIX
    )