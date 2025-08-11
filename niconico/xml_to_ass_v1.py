import xml.etree.ElementTree as ET
import random
import math

# --- 配置项 ---
FILE_NAME = "20250802_ep6_so45239392_filter"
XML_FILE = f'niconico/takop/{FILE_NAME}.xml'  # 替换成你的 XML 文件名
OUTPUT_ASS_FILE = f'niconico/takop/{FILE_NAME}_comments.ass'      # 输出的 ASS 字幕文件名
VIDEO_WIDTH = 1920                      # 你的视频宽度 (像素)
VIDEO_HEIGHT = 1080                     # 你的视频高度 (像素)
BASE_FONT_SIZE = 45                     # 弹幕基准字体大小
SCROLL_DURATION = 16                    # 滚动弹幕的持续时间 (秒)
FIXED_DURATION = 4                      # 顶部/底部/多行固定弹幕的持续时间 (秒)
AVOID_BLOCK_TIME = 4
JIANGE = 0                             # 您可以任意修改此参数，不会影响多行弹幕

# --- 【第1处/共3处 新增改动】为实现“绝对静止”效果所需的配置 ---
NUM_TOP_TRACKS = 8       # 顶部固定轨道的数量
NUM_BOTTOM_TRACKS = 8    # 底部固定轨道的数量
FIXED_LINE_SPACING = 0  # 固定弹幕之间的垂直间距
MARGIN_V = 0            # 固定弹幕区域与屏幕上下边缘的距离
# --- 配置结束 ---

# Niconico 颜色名到 ASS 颜色代码 (&HBBGGRR&) 的映射
COLOR_MAP = {
    'white':  '&HFFFFFF&',
    'red':    '&H0000FF&',
    'pink':   '&HFF8080&',
    'orange': '&H0080FF&',
    'yellow': '&H00FFFF&',
    'green':  '&H00FF00&',
    'cyan':   '&HFFFF00&',
    'blue':   '&HFF0000&',
    'purple': '&HFF00FF&',
    'black':  '&H000000&'
}

def format_time(seconds):
    """将秒数转换为 ASS 的 H:MM:SS.ss 格式"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):01}:{int(m):02}:{int(s):02}.{int((seconds - math.floor(seconds)) * 100):02}"

def create_ass_file():
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"错误: 找不到 XML 文件 '{XML_FILE}'。请检查文件名和路径。")
        return
    except ET.ParseError:
        print(f"错误: XML 文件 '{XML_FILE}' 格式不正确，无法解析。")
        return

    ass_header = f"""
[Script Info]
Title: Generated Comments
ScriptType: v4.00+
WrapStyle: 0
PlayResX: {VIDEO_WIDTH}
PlayResY: {VIDEO_HEIGHT}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei UI,{BASE_FONT_SIZE},&HFFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    track_height = BASE_FONT_SIZE + JIANGE
    num_tracks = VIDEO_HEIGHT // track_height
    # 轨道系统仅用于“普通单行滚动弹幕”
    track_availability = [0.0] * num_tracks
    
    # --- 【第2处/共3处 新增改动】为顶部和底部弹幕创建独立的轨道系统 ---
    top_track_availability = [0.0] * NUM_TOP_TRACKS
    bottom_track_availability = [0.0] * NUM_BOTTOM_TRACKS
    
    with open(OUTPUT_ASS_FILE, 'w', encoding='utf-8') as f:
        f.write(ass_header.strip())

        for chat in root.findall('chat'):
            try:
                vpos_sec = int(chat.get('vpos')) / 100.0
                raw_text = "".join(chat.itertext())
                if not raw_text:
                    continue

                mail = chat.get('mail', '').split()
                is_multiline = '\n' in raw_text
                # 您的原始逻辑：对非多行文本进行替换处理
                processed_text = raw_text.replace('\n', r'\N') if is_multiline else raw_text.replace('\r\n', ' ').replace('\n', ' ')

                is_top = 'ue' in mail
                is_bottom = 'shita' in mail
                
                font_size = BASE_FONT_SIZE
                if 'big' in mail:
                    font_size = int(BASE_FONT_SIZE * 1.25)
                elif 'small' in mail:
                    font_size = int(BASE_FONT_SIZE * 0.8)

                color_hex = '&HFFFFFF&'
                for cmd in mail:
                    if cmd in COLOR_MAP:
                        color_hex = COLOR_MAP[cmd]
                        break

                effects = []
                if color_hex != '&HFFFFFF&': effects.append(f"\\c{color_hex}")
                if font_size != BASE_FONT_SIZE: effects.append(f"\\fs{font_size}")
                
                start_time = vpos_sec
                dialogue_line = ""

                # --- 【第3处/共3处 替换改动】根据弹幕类型分发到不同处理逻辑 ---
                if is_top or is_bottom:
                    # --- 类别1: 顶部/底部固定弹幕 (使用绝对坐标轨道系统) ---
                    end_time = start_time + FIXED_DURATION
                    chosen_track = -1
                    
                    if is_top:
                        track_system = top_track_availability
                        num_tracks_in_system = NUM_TOP_TRACKS
                        for i in range(num_tracks_in_system):
                            if track_system[i] <= start_time:
                                chosen_track = i
                                break
                        if chosen_track == -1:
                            chosen_track = random.randint(0, num_tracks_in_system - 1)
                        
                        y_pos = MARGIN_V + chosen_track * (font_size + FIXED_LINE_SPACING)
                        effects.append(f"\\an8\\pos({VIDEO_WIDTH/2}, {y_pos})")
                        track_system[chosen_track] = end_time

                    else: # is_bottom
                        track_system = bottom_track_availability
                        num_tracks_in_system = NUM_BOTTOM_TRACKS
                        for i in range(num_tracks_in_system):
                            if track_system[i] <= start_time:
                                chosen_track = i
                                break
                        if chosen_track == -1:
                            chosen_track = random.randint(0, num_tracks_in_system - 1)

                        y_pos = VIDEO_HEIGHT - MARGIN_V - chosen_track * (font_size + FIXED_LINE_SPACING)
                        effects.append(f"\\an2\\pos({VIDEO_WIDTH/2}, {y_pos})")
                        track_system[chosen_track] = end_time

                    effect_str = "{" + "".join(effects) + "}"
                    dialogue_line = f"\nDialogue: 1,{format_time(start_time)},{format_time(end_time)},Default,,0,0,0,,{effect_str}{processed_text}"

                elif is_multiline:
                    # --- 类别2: 特殊多行滚动弹幕 (字符画) --- (此部分完全是您v1版本的逻辑)
                    end_time = start_time + SCROLL_DURATION
                    y_pos = VIDEO_HEIGHT / 2
                    lines = processed_text.split(r'\N')
                    max_line_length = max(len(line) for line in lines) if lines else 0
                    text_width = max_line_length * font_size
                    effects.append("\\an5")
                    move_effect = f"\\move({VIDEO_WIDTH + text_width / 2}, {y_pos}, {-text_width / 2}, {y_pos})"
                    effects.append(move_effect)
                    effect_str = "{" + "".join(effects) + "}"
                    dialogue_line = f"\nDialogue: 2,{format_time(start_time)},{format_time(end_time)},Default,,0,0,0,,{effect_str}{processed_text}"
                
                else:
                    # --- 类别3: 普通单行滚动弹幕 --- (此部分完全是您v1版本的逻辑)
                    end_time = start_time + SCROLL_DURATION
                    chosen_track = -1
                    y_pos_offset = 0
                    for i in range(num_tracks):
                        if track_availability[i] <= start_time:
                            chosen_track = i
                            break
                    if chosen_track == -1:
                        chosen_track = min(range(num_tracks), key=lambda i: track_availability[i])
                        y_pos_offset = 0
                    track_availability[chosen_track] = start_time + AVOID_BLOCK_TIME
                    y_pos = (chosen_track * track_height) + y_pos_offset
                    text_width = len(processed_text) * font_size
                    effects.append("\\an7")
                    move_effect = f"\\move({VIDEO_WIDTH}, {y_pos}, {-text_width}, {y_pos})"
                    effects.append(move_effect)
                    effect_str = "{" + "".join(effects) + "}"
                    dialogue_line = f"\nDialogue: 0,{format_time(start_time)},{format_time(end_time)},Default,,0,0,0,,{effect_str}{processed_text}"

                f.write(dialogue_line)

            except (TypeError, ValueError) as e:
                print(f"警告: 跳过一条格式错误的弹幕: chat={chat.attrib}, text='{raw_text[:50]}...', 错误: {e}")
                continue
    
    print(f"成功！增强版 ASS 字幕文件 '{OUTPUT_ASS_FILE}' 已生成。")


if __name__ == '__main__':
    create_ass_file()