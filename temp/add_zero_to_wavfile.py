import os

# --- 使用前请修改 ---
# 请将 'YOUR_FOLDER_PATH' 替换为您的目标文件夹的实际路径
# Windows 示例: r'C:\Users\YourName\Music\Recordings'
# macOS/Linux 示例: r'/Users/YourName/Documents/Audio'
folder_path = r'E:\\抽吧唧\\2\\sub'
# --- 修改结束 ---

def add_prefix_to_wav_files(directory):
    """
    遍历指定目录，为所有 .wav 文件名添加前缀 '0'。
    """
    # 检查路径是否存在
    if not os.path.isdir(directory):
        print(f"错误：文件夹 '{directory}' 不存在。请检查路径是否正确。")
        return

    print(f"正在扫描文件夹: {directory}\n")

    # 遍历文件夹中的所有文件
    for filename in os.listdir(directory):
        # 检查文件是否以 .wav 结尾
        if filename.lower().endswith('.wav'):
            # 构建旧文件的完整路径
            old_file_path = os.path.join(directory, filename)
            
            # 构建新文件名和新文件的完整路径
            new_filename = '0' + filename
            new_file_path = os.path.join(directory, new_filename)
            
            # 重命名文件
            try:
                os.rename(old_file_path, new_file_path)
                print(f'成功: "{filename}"  ->  "{new_filename}"')
            except OSError as e:
                print(f"错误：重命名文件 '{filename}' 时出错: {e}")

    print("\n处理完成！")

# --- 运行脚本 ---
if __name__ == "__main__":
    # 确保用户已经修改了路径
    if 'YOUR_FOLDER_PATH' in folder_path:
        print("请先在脚本中设置您的文件夹路径 'folder_path'。")
    else:
        add_prefix_to_wav_files(folder_path)