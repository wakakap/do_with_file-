import re

def parse_and_print_chat_log(file_path):
    """
    读取并解析一个包含 <chat> 标签的文本文件，
    然后按行交错打印每个 chat 标签内的内容。

    参数:
    file_path (str): 要读取的文件的路径。
    """
    # 步骤 1: 读取文件
    # 我们使用 'try...except' 块来处理文件不存在的常见错误。
    # 'encoding="utf-8"' 确保正确读取文件中的特殊字符。
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：文件 '{file_path}' 未找到。请确保文件路径正确。")
        return

    # 步骤 2: 使用正则表达式提取所有 chat 内容
    # - re.findall 会找到所有匹配项并返回一个列表。
    # - r'<chat.*?>(.*?)</chat>' 是我们的正则表达式模式：
    #   - <chat.*?> 匹配开头的 <chat> 标签及其所有属性。
    #   - (.*?) 是一个非贪婪捕获组，用于捕获标签之间的所有内容，包括换行符。
    #   - </chat> 匹配结束标签。
    # - re.DOTALL 标志让 '.' 特殊字符可以匹配包括换行符在内的任意字符。
    chat_contents = re.findall(r'<chat.*?>(.*?)</chat>', content, re.DOTALL)

    # 步骤 3: 将每个 chat 内容分割成行
    all_chats_lines = []
    max_lines = 0
    for chat in chat_contents:
        # 使用 split('\n') 将字符串分割成一个行的列表。
        lines = chat.split('\n')
        all_chats_lines.append(lines)
        
        # 实时更新我们找到的最大行数，以便知道需要循环多少次。
        if len(lines) > max_lines:
            max_lines = len(lines)

    # 步骤 4: 按行交错打印
    # 外层循环遍历行号（从 0 到 max_lines - 1）。
    for i in range(max_lines):
        # 内层循环遍历我们提取的所有 chat 内容。
        for j in range(all_chats_lines[0][0]):
            for chat_lines in all_chats_lines:
                # 检查当前的 chat 是否有第 i 行。
                # 这可以防止在较短的 chat 内容上出现索引错误。
                if i < len(chat_lines):
                    # 打印该行。
                    # print() 函数会自动在末尾添加换行符。
                    for 
                    print(chat_lines[i])

# --- 如何运行 ---
# 1. 将你的文本内容保存到一个名为 'temp.txt' 的文件中。
# 2. 确保 'temp.txt' 和这个 Python 脚本在同一个目录下。
# 3. 运行这个 Python 脚本。
if __name__ == "__main__":
    file_name = 'niconico/takop/temp.txt'
    parse_and_print_chat_log(file_name)