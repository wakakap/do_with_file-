import os
import sys

def rename_folders_recursively(target_directory):
    """
    递归地遍历指定目录及其所有子目录，如果文件夹名称以'_'结尾，则移除该字符。

    参数:
    target_directory (str): 需要处理的根目录路径。
    """
    if not os.path.isdir(target_directory):
        print(f"错误：提供的路径 '{target_directory}' 不是一个有效的目录。")
        return

    print(f"开始递归扫描目录：'{target_directory}'")

    # 使用 os.walk 进行递归遍历
    # 设置 topdown=False 确保从最深层的子目录开始向上处理。
    # 这样可以安全地重命名目录，而不会影响正在进行的遍历。
    for dirpath, dirnames, filenames in os.walk(target_directory, topdown=False):
        # 遍历当前扫描到的目录下的所有文件夹名
        for name in dirnames:
            # 检查文件夹名称是否以'_'结尾
            if name.endswith('_'):
                # 构建完整的旧路径
                old_path = os.path.join(dirpath, name)
                
                # 构建新的文件夹名称（移除最后一个字符）
                new_name = name[:-1]
                # 构建完整的新路径
                new_path = os.path.join(dirpath, new_name)

                try:
                    # 重命名文件夹
                    os.rename(old_path, new_path)
                    # 输出完整路径以提供更清晰的信息
                    print(f"已重命名: '{old_path}' -> '{new_path}'")
                except OSError as e:
                    print(f"重命名 '{old_path}' 时出错: {e}")

    print("处理完成。")

if __name__ == "__main__":
    # 在此处设置你的目标文件夹路径
    # 注意：请确保路径是正确的，并且你对该路径下的文件有写入权限。
    folder_path = "H:\\BROWSER\\MANGA_PAGES"
    
    # 调用函数
    rename_folders_recursively(folder_path)