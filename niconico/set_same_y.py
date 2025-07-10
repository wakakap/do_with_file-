import re
import os

def process_file(input_path, output_path):
    """
    读取一个文件，扫描并修改指定的 {\move(...)} 指令，然后保存到新文件。

    具体操作：
    - 查找形如 {\move(p1, p2, p3, p4)} 的字符串。
    - 比较参数 p2 和 p4。
    - 如果 p2 和 p4 不相等，则将 p4 修改为 p2。
    - 将修改后的内容写入新文件。

    Args:
        input_path (str): 源文件的路径。
        output_path (str): 保存修改后内容的新文件的路径。
    """
    # 更新正则表达式，使其必须匹配前后的大括号 {}
    # - \{ 和 \} 分别匹配字面量 "{" 和 "}"
    # - \\move\( 匹配字面量 "\move("
    # - ([^,]+)  捕获一个或多个非逗号字符（即第一个参数）
    # - ...      重复上述模式
    # - \)\}       匹配右括号和右大括号
    pattern = re.compile(r'\{\\move\(([^,]+),([^,]+),([^,]+),([^,]+)\)\}')

    def modify_move_command(match):
        """
        这个函数会作为 re.sub 的替换参数。
        它接收一个匹配对象（match object），并返回替换后的字符串。
        """
        # match.group(n) 用于获取第 n 个捕获组的内容。
        # .strip() 用于去除可能存在的前后空格。
        param1 = match.group(1).strip()
        param2 = match.group(2).strip()
        param3 = match.group(3).strip()
        param4 = match.group(4).strip()

        # 比较第二个和第四个参数
        if param2 != param4:
            # 如果不相等，则构建新的字符串，其中第四个参数被替换为第二个参数
            print(f"发现不匹配: {match.group(0)} -> 将第四个参数'{param4}'修改为'{param2}'")
            # 更新返回的字符串，使其也包含大括号
            # 在 f-string 中，要输出一个大括号，需要使用两个大括号 {{ 和 }}
            return f'{{\move({param1}, {param2}, {param3}, {param2})}}'
        else:
            # 如果相等，则无需修改，返回原始匹配到的整个字符串
            return match.group(0)

    try:
        print(f"正在读取文件: {input_path}")
        # 使用 'with' 语句安全地打开文件，并指定 utf-8 编码以支持中文等字符
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:
            
            # 逐行读取源文件
            for line in infile:
                # 对每一行应用正则表达式替换。
                # modify_move_command 函数会对行内所有匹配项进行处理。
                modified_line = pattern.sub(modify_move_command, line)
                # 将处理后（可能未修改）的行写入新文件
                outfile.write(modified_line)

        print("-" * 30)
        print(f"处理完成！结果已保存到新文件: {output_path}")

    except FileNotFoundError:
        print(f"错误：找不到源文件 '{input_path}'。请检查路径是否正确。")
    except Exception as e:
        print(f"处理过程中发生未知错误: {e}")

# --- 主程序入口 ---
if __name__ == "__main__":
    # --- 请在这里配置您的文件路径 ---
    
    # 1. 源文件的路径
    # 例如: "C:/Users/YourUser/Desktop/source_file.txt" (Windows)
    # 或: "/home/user/documents/source_file.txt" (Linux/Mac)
    input_file_path = "niconico/20250708_so45145704_comments_ch.ass" 

    # 2. 修改后要保存的新文件的路径
    # 例如: "C:/Users/YourUser/Desktop/modified_file.txt" (Windows)
    # 或: "/home/user/documents/modified_file.txt" (Linux/Mac)
    output_file_path = "niconico/20250708_so45145704_comments_ch_gai.ass"
    
    # --- 准备一个示例文件用于测试 ---
    # 如果名为 source.txt 的文件不存在，脚本会自动创建一个用于演示。
    if not os.path.exists(input_file_path):
        print(f"未找到 '{input_file_path}', 正在创建一个示例文件用于演示...")
        with open(input_file_path, 'w', encoding='utf-8') as f:
            f.write("第一行：这里有一个需要修改的指令 \\move(2620.0, 110, -700.0, 201)。\n")
            f.write("第二行：这个是正常的，无需修改 \\move(100.0, 50, -200.0, 50)。\n")
            f.write("第三行：这是另一个不匹配的例子 \\move(1, 2, 3, 4)。\n")
            f.write("第四行没有任何指令。\n")
            f.write("第五行有两个指令：\\move(10, 20, 30, 40) 和 \\move(50, 60, 70, 60)。\n")
        print(f"示例文件 '{input_file_path}' 创建成功。")
        print("-" * 30)

    # 调用核心函数来处理文件
    process_file(input_file_path, output_file_path)