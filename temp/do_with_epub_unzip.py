import os
import shutil
from tkinter import Tk, filedialog

def organize_and_clean_comic_folders(root_dir):
    """
    遍历指定根目录下的所有子文件夹，仅保留 'item/image' 中的文件，
    并删除该子文件夹内所有其他原始文件和目录。
    """
    print(f"开始处理文件夹: {root_dir}\n")
    
    if not os.path.isdir(root_dir):
        print(f"错误: 路径 '{root_dir}' 不存在或不是一个文件夹。")
        return

    # 遍历根目录下的所有项目（即每个漫画卷的文件夹）
    for volume_folder_name in os.listdir(root_dir):
        volume_path = os.path.join(root_dir, volume_folder_name)
        
        # 确保处理的是文件夹
        if os.path.isdir(volume_path):
            image_source_path = os.path.join(volume_path, 'item', 'image')
            
            # 检查源图片文件夹是否存在
            if os.path.isdir(image_source_path):
                print(f"正在处理: {volume_folder_name}")

                try:
                    # 步骤1: 记录下所有需要删除的原始顶层项目
                    original_items = os.listdir(volume_path)
                    
                    # 步骤2: 将所有图片从 item/image 移动到卷文件夹根目录
                    image_files_moved = []
                    for filename in os.listdir(image_source_path):
                        src_file = os.path.join(image_source_path, filename)
                        # 确保是文件再移动
                        if os.path.isfile(src_file):
                            shutil.move(src_file, volume_path)
                            image_files_moved.append(filename)

                    if image_files_moved:
                        print(f"  - {len(image_files_moved)} 张图片移动完成。")
                    else:
                        print(f"  - 'item/image' 文件夹为空，未移动图片。")

                    # 步骤3: 删除所有原始顶层项目
                    print(f"  - 正在清理其他所有文件和文件夹...")
                    for item_name in original_items:
                        item_path = os.path.join(volume_path, item_name)
                        try:
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                            else: # 是文件
                                os.remove(item_path)
                        except OSError as e:
                            print(f"    - 清理 {item_path} 时出错: {e}")
                    
                    print(f"  - 清理完成。")

                except Exception as e:
                    print(f"  - 处理 '{volume_folder_name}' 时发生意外错误: {e}")
                
                print("-" * 20)

    print("\n所有文件夹处理完毕！")


if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    
    print("请在弹出的窗口中选择需要处理的根文件夹 (例如 '作品名')...")
    
    selected_directory = filedialog.askdirectory(
        title="请选择包含漫画卷的根文件夹"
    )
    
    if selected_directory:
        organize_and_clean_comic_folders(selected_directory)
    else:
        print("未选择文件夹，程序已取消。")
        
    input("\n按 Enter 键退出...")