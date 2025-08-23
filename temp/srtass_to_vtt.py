import os
import subprocess
import sys

def convert_subtitles_to_vtt(root_folder):
    """
    Recursively scans a directory for .srt and .ass files and converts them 
    to .vtt format using ffmpeg.

    Args:
        root_folder (str): The absolute path to the folder to be scanned.
    """
    # 检查指定的路径是否存在且是一个文件夹
    if not os.path.isdir(root_folder):
        print(f"错误：提供的路径 '{root_folder}' 不是一个有效的文件夹。")
        return

    print(f"--- 开始扫描文件夹：{root_folder} ---")
    
    converted_count = 0
    skipped_count = 0
    error_count = 0

    # 定义支持的输入字幕格式
    supported_formats = ('.srt', '.ass')

    # 使用 os.walk 遍历所有子目录和文件
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            # 检查文件是否为支持的字幕格式（忽略大小写）
            if filename.lower().endswith(supported_formats):
                input_path = os.path.join(dirpath, filename)
                # 构建对应的 .vtt 文件路径
                vtt_path = os.path.splitext(input_path)[0] + ".vtt"

                # 检查是否已经存在对应的 .vtt 文件
                if os.path.exists(vtt_path):
                    print(f"⏭️  已跳过（.vtt 文件已存在）：{filename}")
                    skipped_count += 1
                    continue
                
                print(f"⏳  正在转换：{filename} ...")

                try:
                    # 构建并执行 ffmpeg 命令
                    command = [
                        'ffmpeg',
                        '-i', input_path,
                        '-y',
                        vtt_path
                    ]
                    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    print(f"✅  转换成功 -> {os.path.basename(vtt_path)}")
                    converted_count += 1
                    
                    # --- !! 安全警告 !! ---
                    # 如果您希望在转换成功后自动删除原始的字幕文件 (.srt 或 .ass)，
                    # 请取消下面这行代码的注释（即删除行首的 '#' 和空格）。
                    # 在确认脚本运行正常前，请勿启用此功能。
                    #
                    # os.remove(input_path)
                    # print(f"🗑️  已删除原始文件：{filename}")

                except subprocess.CalledProcessError as e:
                    print(f"❌  转换失败：{filename}。FFmpeg 返回了错误。")
                    error_count += 1
                except FileNotFoundError:
                    print("❌ 错误：找不到 'ffmpeg' 命令。请确保 FFmpeg 已经安装并添加到了系统的 PATH 环境变量中。")
                    return
                except Exception as e:
                    print(f"❌ 发生未知错误：{filename}。错误信息：{e}")
                    error_count += 1

    print("\n--- 任务完成 ---")
    print(f"转换成功: {converted_count} 个文件")
    print(f"跳过: {skipped_count} 个文件")
    print(f"失败: {error_count} 个文件")
    print("---------------")


if __name__ == "__main__":
    # 检查是否从命令行提供了文件夹路径
    target_folder = "H:\\BROWSER\\ANIME_PAGES\\監獄学園（プリズンスクール）"
    convert_subtitles_to_vtt(target_folder)
