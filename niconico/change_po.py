# -*- coding: utf-8 -*-

# --- 文件路径设置 ---
# 输入文件名（原始文件）
input_filename = 'niconico/takop/merged_file - 副本.txt'
# 输出文件名（保存交换后的内容）
output_filename = 'niconico/takop/merged_file.txt'

def swap_comma_content(input_file, output_file):
    """
    读取一个文件，交换每行第一个逗号前后的内容，并写入新文件。

    Args:
        input_file (str): 输入文件的路径。
        output_file (str): 输出文件的路径。
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as fin, \
             open(output_file, 'w', encoding='utf-8') as fout:
            
            print(f"正在读取文件: {input_file}")
            
            for line in fin:
                # 去除行末的换行符和首尾的空白字符
                stripped_line = line.strip()
                
                # 检查行中是否包含逗号
                if ',' in stripped_line:
                    # 使用 .split(',', 1) 按第一个逗号分割成两部分
                    # 这可以确保即使一行中有多个逗号，也只处理第一个
                    parts = stripped_line.split(',', 1)
                    
                    # 交换位置
                    # parts[0] 是逗号前的内容, parts[1] 是逗号后的内容
                    swapped_line = f"{parts[1]},{parts[0]}"
                    
                    # 将交换后的行写入新文件，并加上换行符
                    fout.write(swapped_line + '\n')
                else:
                    # 如果行中没有逗号，则直接将原行写入新文件
                    fout.write(stripped_line + '\n')
                    
        print(f"处理完成！结果已保存到: {output_filename}")

    except FileNotFoundError:
        print(f"错误：找不到文件 '{input_file}'。请检查文件名和路径是否正确。")
    except Exception as e:
        print(f"处理过程中发生错误: {e}")

# --- 执行函数 ---
if __name__ == "__main__":
    swap_comma_content(input_filename, output_filename)