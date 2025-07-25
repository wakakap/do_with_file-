import sys
import re

def renumber_srt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：文件 '{file_path}' 未找到。")
        return
    except Exception as e:
        print(f"读取文件时出错：{e}")
        return

    # 使用正则表达式按字幕块（序号、时间、文本）分割文件
    # 每个块由一个数字、一个时间戳和文本组成，块之间由一个或多个空行分隔
    subtitle_blocks = re.split(r'\n\s*\n', content.strip())

    new_srt_content = []
    new_index = 1

    for block in subtitle_blocks:
        if block.strip():
            # 将块按行分割
            lines = block.strip().split('\n')
            
            # 第一个是旧序号，第二个是时间戳，其余是字幕文本
            if len(lines) >= 2:
                # 用新的序号替换旧的序号
                new_block = f"{new_index}\n" + "\n".join(lines[1:])
                new_srt_content.append(new_block)
                new_index += 1

    # 定义新文件名
    output_file_path = file_path.rsplit('.', 1)[0] + '_reordered.srt'

    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            # 用两个换行符连接每个块，以符合SRT格式
            f.write('\n\n'.join(new_srt_content) + '\n')
        print(f"处理完成！已将重新编号的字幕保存到：'{output_file_path}'")
    except Exception as e:
        print(f"写入文件时出错：{e}")

if __name__ == "__main__":
    input_file = "E:\\抽吧唧\\看章鱼反应\\4.srt"
    renumber_srt(input_file)