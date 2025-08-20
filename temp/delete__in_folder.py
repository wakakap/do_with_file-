import os
import sys

def rename_items_recursively(target_directory):
    """
    递归地遍历指定目录及其所有子目录，
    如果文件夹或文件的名称以'_'结尾，则移除该字符。

    参数:
    target_directory (str): 需要处理的根目录路径。
    """
    if not os.path.isdir(target_directory):
        print(f"错误：提供的路径 '{target_directory}' 不是一个有效的目录。")
        return

    print(f"开始递归扫描目录：'{target_directory}'")

    # 使用 os.walk 进行递归遍历
    # 设置 topdown=False 确保从最深层的子目录开始向上处理，
    # 这样可以安全地重命名目录，而不会影响正在进行的遍历。
    for dirpath, dirnames, filenames in os.walk(target_directory, topdown=False):
        
        # --- 步骤 1: 处理当前目录下的文件 ---
        for filename in filenames:
            if filename.endswith('_'):
                old_path = os.path.join(dirpath, filename)
                new_name = filename[:-1]
                new_path = os.path.join(dirpath, new_name)

                try:
                    # 重命名文件
                    os.rename(old_path, new_path)
                    print(f"已重命名文件: '{old_path}' -> '{new_path}'")
                except OSError as e:
                    print(f"重命名文件 '{old_path}' 时出错: {e}")

        # --- 步骤 2: 处理当前目录下的文件夹 ---
        for dirname in dirnames:
            if dirname.endswith('_'):
                old_path = os.path.join(dirpath, dirname)
                new_name = dirname[:-1]
                new_path = os.path.join(dirpath, new_name)

                try:
                    # 重命名文件夹
                    os.rename(old_path, new_path)
                    print(f"已重命名文件夹: '{old_path}' -> '{new_path}'")
                except OSError as e:
                    print(f"重命名文件夹 '{old_path}' 时出错: {e}")

    print("处理完成。")

if __name__ == "__main__":
    # 在此处设置你的目标文件夹路径
    # 注意：请确保路径是正确的，并且你对该路径下的文件有写入权限。
    folder_path = "H:\\BROWSER\\MANGA_COVER"
    
    # 调用函数
    rename_items_recursively(folder_path)