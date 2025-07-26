import xml.etree.ElementTree as ET
import random
import math

## ffmpeg -i "pr.mp4" -vf "ass=20250708_so45145704_comments_ch_gai_extend.ass" -c:a copy output2.mp4
## ffmpeg -i "ANi_章魚嗶的原罪_02_1080PBahaWEB_DLAAC_AVCCHT.mp4" -vf "ass=20250708_so45145704_comments_ch_gai.ass,minterpolate=fps=60" -c:v libx264 -crf 19 -preset slow -c:a copy output.mp4
## ffmpeg -i "ANi_章魚嗶的原罪_02_1080PBahaWEB_DLAAC_AVCCHT.mp4" -vf "minterpolate=fps=60:mi_mode=blend:scd=1" "video.mp4"
## ffmpeg -i nullsrc=s=1920x1080 -vf "ass=20250708_so45145704_comments_ch_gai_extend.ass" ass.mov

# --- 配置项 ---
FILE_NAME = "20250727_ep1_so29416460"
XML_FILE = f'niconico/higurashi/{FILE_NAME}.xml'  # 替换成你的 XML 文件名
OUTPUT_ASS_FILE = f'niconico/higurashi/{FILE_NAME}_comments.ass'     # 输出的 ASS 字幕文件名
VIDEO_WIDTH = 1920                   # 你的视频宽度 (像素)
VIDEO_HEIGHT = 1080                  # 你的视频高度 (像素)
BASE_FONT_SIZE = 45                  # 弹幕基准字体大小
SCROLL_DURATION = 16                  # 滚动弹幕的持续时间 (秒)
FIXED_DURATION = 4                   # 顶部/底部固定弹幕的持续时间 (秒)
AVOID_BLOCK_TIME =  4 
JIANGE = 8               
# --- 配置结束 ---

# Niconico 颜色名到 ASS 颜色代码 (&HBBGGRR&) 的映射
# ASS 的颜色格式是 蓝-绿-红 (BGR) 的十六进制
COLOR_MAP = {
    'white':   '&HFFFFFF&',
    'red':     '&H0000FF&',
    'pink':    '&HFF8080&',
    'orange':  '&H0080FF&',
    'yellow':  '&H00FFFF&',
    'green':   '&H00FF00&',
    'cyan':    '&HFFFF00&',
    'blue':    '&HFF0000&',
    'purple':  '&HFF00FF&',
    'black':   '&H000000&'
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
    
    # 弹幕轨道，仅用于防止滚动弹幕重叠
    num_tracks = VIDEO_HEIGHT // (BASE_FONT_SIZE + JIANGE)
    track_availability = [0.0] * num_tracks
    
    with open(OUTPUT_ASS_FILE, 'w', encoding='utf-8') as f:
        f.write(ass_header.strip())

        for chat in root.findall('chat'):
            try:
                vpos_sec = int(chat.get('vpos')) / 100.0
                # text = chat.text
                text = "".join(chat.itertext()).replace('\r\n', ' ').replace('\n', ' ')
                mail = chat.get('mail', '').split() # 获取 mail 命令列表

                if not text:
                    continue

                # --- 解析 mail 命令 ---
                is_top = 'ue' in mail
                is_bottom = 'shita' in mail
                
                font_size = BASE_FONT_SIZE
                if 'big' in mail:
                    font_size = int(BASE_FONT_SIZE * 1.25)
                elif 'small' in mail:
                    font_size = int(BASE_FONT_SIZE * 0.8)

                color_hex = '&HFFFFFF&' # 默认白色
                for cmd in mail:
                    if cmd in COLOR_MAP:
                        color_hex = COLOR_MAP[cmd]
                        break # 找到第一个颜色就停止

                # --- 构建 ASS 行 ---
                start_time = vpos_sec
                dialogue_line = ""
                
                # 构建特效标签字符串
                effects = []
                if color_hex != '&HFFFFFF&': # 如果不是默认白色，添加颜色标签
                    effects.append(f"\\c{color_hex}")
                if font_size != BASE_FONT_SIZE: # 如果不是默认大小，添加字号标签
                    effects.append(f"\\fs{font_size}")
                
                # 根据位置（滚动、顶部、底部）生成不同的特效
                if is_top or is_bottom:
                    # 对于顶部或底部固定的弹幕
                    end_time = start_time + FIXED_DURATION
                    if is_top:
                        effects.append("\\an8") # an8 = 顶部居中对齐
                    else: # is_bottom
                        effects.append("\\an2") # an2 = 底部居中对齐
                    
                    effect_str = "{" + "".join(effects) + "}"
                    dialogue_line = f"\nDialogue: 0,{format_time(start_time)},{format_time(end_time)},Default,,0,0,0,,{effect_str}{text}"

                else:
                    # 对于滚动弹幕 (默认)
                    end_time = start_time + SCROLL_DURATION
                    
                    # 寻找一个可用的垂直轨道来避免重叠
                    chosen_track = -1
                    for i in range(num_tracks):
                        if track_availability[i] <= start_time:
                            chosen_track = i
                            break
                    if chosen_track == -1:
                        chosen_track = random.randint(0, num_tracks - 1)
                    
                    # 更新此轨道的占用时间
                    track_availability[chosen_track] = start_time + AVOID_BLOCK_TIME # 假设弹幕进入屏幕需要2秒
                    
                    y_pos = (chosen_track * (font_size + 10)) + font_size
                    text_width = len(text) * font_size
                    
                    move_effect = f"\\move({VIDEO_WIDTH + text_width / 2}, {y_pos}, {-text_width / 2}, {y_pos})"
                    effects.append(move_effect)
                    
                    effect_str = "{" + "".join(effects) + "}"
                    dialogue_line = f"\nDialogue: 0,{format_time(start_time)},{format_time(end_time)},Default,,0,0,0,,{effect_str}{text}"

                f.write(dialogue_line)

            except (TypeError, ValueError) as e:
                print(f"警告: 跳过一条格式错误的弹幕: {chat.attrib}, 错误: {e}")
                continue
    
    print(f"成功！增强版 ASS 字幕文件 '{OUTPUT_ASS_FILE}' 已生成。")


if __name__ == '__main__':
    create_ass_file()