import os

def remove_lines_with_move(input_path):
    """
    读取一个文件，删除所有包含 "\\move" 的行，
    并将结果保存到一个新文件中。

    Args:
        input_path (str): 输入文件的路径。
    """
    # 检查输入文件是否存在
    if not os.path.exists(input_path):
        print(f"错误：文件 '{input_path}' 不存在。")
        return

    # 构建输出文件名
    directory, filename = os.path.split(input_path)
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}_deletemove{ext}"
    output_path = os.path.join(directory, output_filename)

    try:
        # 使用 'utf-8-sig' 来正确处理可能存在的 BOM
        with open(input_path, 'r', encoding='utf-8-sig') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:
            
            lines_deleted = 0
            for line in infile:
                # 检查行中是否包含 "\move"
                if "\\move" in line:
                    lines_deleted += 1
                    # 如果包含，则跳过此行，不写入新文件
                    continue
                # 否则，将原行写入新文件
                outfile.write(line)

        print(f"处理完成！")
        print(f"已删除 {lines_deleted} 行。")
        print(f"修改后的文件已保存为：{output_path}")

    except Exception as e:
        print(f"处理文件时发生错误：{e}")

# --- 使用方法 ---
if __name__ == "__main__":
    # 1. 将下面的 'path/to/your/file.ass' 替换为你的实际文件路径
    #    例如在 Windows 上: "C:\\Users\\YourUser\\Documents\\subtitle.ass"
    #    或在 macOS/Linux 上: "/Users/YourUser/Documents/subtitle.ass"
    # 2. 运行此脚本
    
    # 替换为你的 ASS 文件路径
    target_file_path = 'niconico/higurashi/20250727_ep1_so29416460_comments.ass' 
    
    remove_lines_with_move(target_file_path)