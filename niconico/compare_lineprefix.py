import string
def get_content_to_compare(line: str) -> str:
    """
    获取用于比较的内容。
    逻辑：找到第9个逗号之后、最后一个 '}' 之前的内容。
    """
    # 步骤 1: 找到第9个逗号的索引
    parts = line.split(',', 9)  # 最多分割9次，会产生10个部分
    
    # 如果分割后的部分少于10个，说明没有9个逗号
    if len(parts) < 10:
        # 如果找不到9个逗号，按照一个安全的回退策略，
        # 比如比较整行（去除首尾空格），或者返回空字符串。
        # 这里我们选择返回整行，与您原始代码的回退逻辑类似。
        return line.strip()
    
    # 第9个逗号的位置就在第9个部分的结尾处
    # 我们需要计算出它在原始字符串中的索引
    # len(line) - len(parts[-1]) - 1 即可得到第9个逗号的索引
    ninth_comma_index = len(line) - len(parts[-1]) - 1

    # 步骤 2: 从第9个逗号之后，反向查找最后一个 '}'
    # str.rfind() 是查找子字符串最后一次出现的位置
    # 第二个参数表示搜索的起始位置
    last_brace_index = line.rfind('}', ninth_comma_index)

    # 如果在第9个逗号之后没有找到 '}'
    if last_brace_index == -1:
        # 同样采取回退策略
        return line.strip()
        
    # 步骤 3: 返回 '}' 之前的所有内容
    return line[:last_brace_index]

def find_first_differing_line(file1_path, file2_path):
    """
    比较两个文本文件，找出第一个在“非英文或标点符号”之前内容不一致的行。

    Args:
        file1_path (str): 第一个文本文件的路径。
        file2_path (str): 第二个文本文件的路径。

    Returns:
        int: 第一个不一致的行号。如果未找到不一致的行，则返回 None。
        str: 如果发生文件错误，则返回错误信息。
    """
    # 允许的字符集：英文字母、标点符号、空格
    allowed_chars = set(string.ascii_letters + string.punctuation + ' ')

    try:
        with open(file1_path, 'r', encoding='utf-8') as f1, \
            open(file2_path, 'r', encoding='utf-8') as f2:

            for line_num, (line1, line2) in enumerate(zip(f1, f2), 1):
                
                # 使用新的逻辑函数获取要比较的内容
                content_to_compare1 = get_content_to_compare(line1)
                content_to_compare2 = get_content_to_compare(line2)

                # 如果提取出的内容不一致，立即返回当前行号
                if content_to_compare1 != content_to_compare2:
                    # 假设这段代码是在一个函数中，使用 return
                    # 如果不是，您可能想用 print(line_num) 并 break
                    return line_num 

    except FileNotFoundError:
        return f"错误：文件未找到。请检查路径 '{file1_path}' 或 '{file2_path}'。"
    except Exception as e:
        return f"发生错误：{e}"

    # 如果循环正常结束（文件内容都一致），则返回 None
    return None

if __name__ == "__main__":
    file1 = 'niconico/20250708_so45145704_comments.ass'
    file2 = 'niconico/20250708_so45145704_comments_ch.ass'
    result = find_first_differing_line(file1, file2)

    if isinstance(result, list):
        if result:
            print(f"在以下行中发现内容不一致：{result}")
        else:
            print("两个文件在指定规则下内容一致。")
    else:
        print(result)