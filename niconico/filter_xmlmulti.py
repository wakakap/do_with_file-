import xml.etree.ElementTree as ET
import os

def deduplicate_xml_comments(input_file, output_file):
    """
    读取XML弹幕文件，根据 user_id 和内容去重，并保存为新文件。

    :param input_file: 输入的XML文件名 (例如 'danmaku.xml')
    :param output_file: 输出的XML文件名 (例如 'danmaku_unique.xml')
    """
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：找不到输入文件 '{input_file}'")
        return

    try:
        # 解析整个XML树
        tree = ET.parse(input_file)
        root = tree.getroot()

        # 创建一个新的根节点，用于存放去重后的内容
        # 我们复制原始根节点的标签和属性
        new_root = ET.Element(root.tag, root.attrib)

        # 使用一个集合来存储已经见过的 (user_id, content) 组合，用于高效去重
        seen_comments = set()

        # 遍历根节点下的所有子元素 (即 <chat> 标签)
        for comment_element in root:
            # 确保我们只处理 <chat> 标签
            if comment_element.tag == 'chat':
                user_id = comment_element.get('user_id')
                content = comment_element.text or "" # 如果内容为空，则使用空字符串

                # 创建一个元组作为唯一标识符
                comment_identity = (user_id, content)

                # 如果这个标识符还没有在集合中，说明是第一次出现
                if comment_identity not in seen_comments:
                    # 将其添加到集合中，表示我们已经处理过它了
                    seen_comments.add(comment_identity)
                    # 将这个不重复的元素添加到新的根节点下
                    new_root.append(comment_element)
            else:
                # 如果文件中还有其他类型的标签，也直接保留
                new_root.append(comment_element)

        # 创建一个新的树对象
        new_tree = ET.ElementTree(new_root)

        # 将新的树写入到输出文件
        # encoding='utf-8' 对于处理像'うぽつ'这样的非英文字符至关重要
        # xml_declaration=True 会在文件开头写入 <?xml version="1.0" ... ?>
        new_tree.write(output_file, encoding='utf-8', xml_declaration=True)

        print(f"处理完成！")
        print(f"原始文件 '{input_file}' 中共有 {len(root)} 条弹幕。")
        print(f"去重后剩下 {len(new_root)} 条弹幕。")
        print(f"结果已保存到新文件 '{output_file}' 中。")

    except ET.ParseError as e:
        print(f"错误：解析XML文件 '{input_file}' 失败。请检查文件格式是否正确。")
        print(f"错误详情: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")


# --- 主程序入口 ---
if __name__ == "__main__":
    # --- 请在这里修改您的文件名 ---
    input_filename = 'niconico/takop/20250802_ep6_so45239392.xml'  # 替换成你的原始文件名
    output_filename = 'niconico/takop/20250802_ep6_so45239392_filter.xml' # 这是将要创建的新文件名

    # 调用函数执行去重操作
    deduplicate_xml_comments(input_filename, output_filename)