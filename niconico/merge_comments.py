# 帮我写一个python脚本对弹幕文件ass文件进行处理，然后把修改后的ass文件保存下来。具体分析形如 Dialogue: 0,0:00:12.25,0:00:25.25,Default,,0,0,0,,{\move(2020.0, 410, -100.0, 410)}可爱 的行，必须有\move才会计入。扫描这些行的时间，并计算每个在屏幕上的开始和离开时间，然后选择时间筛选t从0秒开始直到第30分钟逐秒增加，如果每次增加一秒就判断这个时刻是否在这些带有\move的行的开始和结束时间范围内，如果在，可以用个列表flag[]记录，如果在范围内的行的数量超过了参数thread=10个，则把前10个行删除，用一个字体大小是100的相同内容的弹幕来取代这10个，其移动时间等参数取满足的10行中的第一行的参数。并且再用一个变量储存这些大的弹幕，使得之后的计数中忽略他们。由于从上到下的弹幕进入时间是递增的，你在扫描时可能有些可简化的算法。有点小困难，但请加油，给我实现的python代码
import re
from datetime import timedelta
import os
from collections import defaultdict

# --- 辅助函数和类 (无变化) ---
def parse_ass_time(time_str: str) -> timedelta:
    parts = time_str.split(':')
    h = int(parts[0]); m = int(parts[1]); s_ms = parts[2].split('.')
    s = int(s_ms[0]); cs = int(s_ms[1])
    return timedelta(hours=h, minutes=m, seconds=s, milliseconds=cs * 10)

def format_ass_time(td: timedelta) -> str:
    total_seconds = td.total_seconds()
    h = int(total_seconds // 3600); m = int((total_seconds % 3600) // 60)
    s = int(total_seconds % 60); cs = int((td.microseconds / 10000) % 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def set_font_size(text_field: str, size: int) -> str:
    fs_pattern = re.compile(r'(\\fs)(\d+(\.\d+)?)')
    if fs_pattern.search(text_field):
        return fs_pattern.sub(fr'\1{size}', text_field)
    else:
        override_match = re.match(r'(\{.*?\})', text_field)
        if override_match:
            block = override_match.group(1)
            new_block = block[:-1] + f'\\fs{size}' + '}'
            return new_block + text_field[override_match.end():]
        else:
            return f'{{\\fs{size}}}{text_field}'

class SubtitleLine:
    def __init__(self, line_str: str = None):
        self.is_valid = False
        if line_str and line_str.startswith("Dialogue:"):
            try:
                self.prefix = "Dialogue: "
                self.parts = line_str[len(self.prefix):].split(',', 9)
                self.start_time_td = parse_ass_time(self.parts[1])
                self.end_time_td = parse_ass_time(self.parts[2])
                self.is_valid = True
            except Exception as e:
                self.is_valid = False
    
    @property
    def text_field(self) -> str: return self.parts[9]
    @text_field.setter
    def text_field(self, value: str): self.parts[9] = value
    @property
    def content_text(self) -> str:
        full_text = self.text_field
        return full_text.rsplit('}', 1)[1] if '}' in full_text else full_text

    def to_string(self) -> str:
        self.parts[1] = format_ass_time(self.start_time_td)
        self.parts[2] = format_ass_time(self.end_time_td)
        return self.prefix + ",".join(self.parts)
    def clone(self): return SubtitleLine(self.to_string())

# --- 核心处理函数 (已更新为while循环) ---
def process_ass_file(input_path: str, output_path: str, thread: int = 10, max_minutes: int = 30):
    print(f"开始处理文件: {input_path}")
    header_and_styles, dialogue_objects = [], []
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            is_event_section = False
            for line in f:
                stripped_line = line.strip()
                if stripped_line == '[Events]': is_event_section = True
                if is_event_section and stripped_line.startswith('Dialogue:'):
                    subtitle = SubtitleLine(stripped_line)
                    if subtitle.is_valid: dialogue_objects.append(subtitle)
                else:
                    header_and_styles.append(line)
    except Exception as e:
        print(f"文件读取错误: {e}"); return

    move_lines = [line for line in dialogue_objects if r'\move' in line.text_field]
    static_lines = [line for line in dialogue_objects if r'\move' not in line.text_field]
    move_lines.sort(key=lambda x: x.start_time_td)
    print(f"共找到 {len(move_lines)} 条移动弹幕和 {len(static_lines)} 条其他弹幕。")

    processed_indices, newly_created_lines = set(), []
    max_scan_time_seconds = max_minutes * 60

    for t_sec in range(max_scan_time_seconds):
        current_time = timedelta(seconds=t_sec)
        active_groups = defaultdict(list)
        
        for i, line in enumerate(move_lines):
            if i in processed_indices: continue
            if line.start_time_td > current_time: break
            if line.start_time_td <= current_time < line.end_time_td:
                active_groups[line.content_text].append(i)
        
        # --- 【核心逻辑修改部分：IF 改为 WHILE】 ---
        for content, indices_list in active_groups.items():
            unprocessed_indices = [idx for idx in indices_list if idx not in processed_indices]
            
            # 使用 while 循环，只要未处理的弹幕数量还够，就一直合并
            while len(unprocessed_indices) >= thread:
                print(f"在 {current_time} 检测到内容为 '{content}' 的弹幕 {len(unprocessed_indices)} 条 (超过/等于 {thread})。正在循环合并...")
                
                # 1. 取出当前批次的进行合并
                indices_to_replace = unprocessed_indices[:thread]
                
                # 2. 将这些索引加入黑名单
                for idx in indices_to_replace:
                    processed_indices.add(idx)
                
                # 3. 创建大弹幕
                template_line = move_lines[indices_to_replace[0]]
                new_big_line = template_line.clone()
                new_big_line.text_field = set_font_size(new_big_line.text_field, 100)
                newly_created_lines.append(new_big_line)
                
                # 4. 从未处理列表中移除刚刚处理过的，准备下一次while循环
                unprocessed_indices = unprocessed_indices[thread:]
    
    final_dialogue_lines = static_lines
    for i, line in enumerate(move_lines):
        if i not in processed_indices:
            final_dialogue_lines.append(line)
    final_dialogue_lines.extend(newly_created_lines)
    final_dialogue_lines.sort(key=lambda x: x.start_time_td)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(header_and_styles)
            for line in final_dialogue_lines:
                f.write(line.to_string() + '\n')
    except Exception as e:
        print(f"文件写入错误: {e}"); return

    print("-" * 20)
    print("处理完成！")
    print(f"修改后的文件已保存至: {output_path}")


if __name__ == '__main__':
    # 请将 'your_input_file.ass' 替换为你的实际文件名
    input_file = 'niconico/takop/20250802_ep6_2万+_so45239392_filter_comments_ch.ass'
    
    # 检查示例文件是否存在，如果不存在则创建一个

    # 定义输出文件名
    output_file = 'niconico/takop/20250802_ep6_2万+_so45239392_filter_comments_ch_merge.ass'
    
    # 执行处理函数
    # 你可以修改这里的参数，例如将 thread 改为 5，或将 max_minutes 改为 10
    process_ass_file(
        input_path=input_file,
        output_path=output_file,
        thread=8,
        max_minutes=27
    )