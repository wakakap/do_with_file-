# gemini_ass_processor.py (v3 - CLI with Cache)
import google.generativeai as genai
import os
import time
from dotenv import load_dotenv

# --- 用户配置区域 ---
INPUT_ASS_PATH = "niconico/20250708_so45145704_comments.ass" 

# 从第几行开始处理。设置为 1 表示从头开始。
START_LINE = 1

# --- AI 与系统配置 ---

# 系统提示，告诉AI该做什么。
# 您可以修改它以改变AI的行为 (例如，翻译风格、总结、校对等)。
SYSTEM_PROMPT = """
这是一句日本ニコニコ動画上的评论，请用符合的语气把它翻译成中文。注意保留特殊字符。不要说其它废话，直接给我翻译结果：
"""

# 缓存文件名
CACHE_FILE = "niconico/temp.txt"
# 缓存文件分隔符
CACHE_DELIMITER = "|||"

# 每次API调用之间的延迟（秒），以避免速率限制。
# 'gemini-1.5-flash' 模型的免费额度很高 (60 QPM)，1秒是安全的。
API_CALL_DELAY = 1

# --- 核心功能 ---

def initialize_gemini():
    """
    从 .env 文件加载API密钥并初始化Gemini模型。
    如果初始化失败，则返回 None。
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("错误: 在 .env 文件中未找到 GEMINI_API_KEY。")
        print("请创建一个名为 .env 的文件，并将您的API密钥添加进去 (GEMINI_API_KEY=xxxx)。")
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("Gemini 模型初始化成功。")
        return model
    except Exception as e:
        print(f"初始化 Gemini 时出错: {e}")
        return None

def load_translation_cache(file_path):
    """
    加载翻译缓存文件到字典中。
    文件格式: original_text|||translated_text
    """
    cache = {}
    if not os.path.exists(file_path):
        print("缓存文件 temp.txt 不存在，将创建一个新的。")
        return cache
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(CACHE_DELIMITER, 1)
                if len(parts) == 2:
                    original, translated = parts
                    cache[original] = translated
        print(f"从 {file_path} 加载了 {len(cache)} 条缓存记录。")
    except Exception as e:
        print(f"读取缓存文件时出错: {e}")
    return cache

def get_gemini_response(model, text_to_process):
    """
    将文本连同系统提示发送到Gemini API，并返回响应。
    """
    if not model:
        raise ValueError("Gemini 模型未初始化。")
    if not text_to_process.strip():
        # 不为空文本调用API
        return ""
    
    full_prompt = [
        SYSTEM_PROMPT,
        text_to_process
    ]
    
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"  -> API 错误: {e}")
        # 失败时返回原文以避免数据丢失
        return text_to_process

def parse_dialogue_line(line):
    """
    解析ASS对话行，以分离元数据前缀、样式标签和实际文本。
    ASS 格式: Dialogue: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,{style}Text
    
    返回元组: (dialogue_prefix, style_tags, actual_text)
    如果不是有效的对话行，则返回 (None, None, None)。
    """
    if not line.startswith("Dialogue:"):
        return None, None, None
        
    parts = line.strip().split(',', 9)
    if len(parts) < 10:
        return None, None, None
        
    dialogue_prefix = ",".join(parts[:9])
    raw_text_field = parts[9]
    
    style_end_index = raw_text_field.rfind('}')
    
    if style_end_index != -1:
        style_tags = raw_text_field[:style_end_index + 1]
        actual_text = raw_text_field[style_end_index + 1:]
    else:
        style_tags = ""
        actual_text = raw_text_field
            
    return dialogue_prefix, style_tags, actual_text

def process_ass_file(input_path, output_path, start_line=1):
    """
    读取输入的ASS文件，使用Gemini（或缓存）处理对话行，
    并将结果写入输出文件。
    """
    gemini_model = initialize_gemini()
    if not gemini_model:
        return

    # 加载已有的翻译缓存
    translation_cache = load_translation_cache(CACHE_FILE)

    print(f"\n开始处理文件: {input_path}")
    print(f"输出将保存至: {output_path}")
    if start_line > 1:
        print(f"从第 {start_line} 行开始处理。")

    current_line_num = 0
    try:
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile, \
             open(CACHE_FILE, 'a', encoding='utf-8') as cache_file: # 以追加模式打开缓存文件
            
            for line in infile:
                current_line_num += 1
                if current_line_num < start_line:
                    outfile.write(line)
                    outfile.flush()
                    continue

                dialogue_prefix, style_tags, text_to_process = parse_dialogue_line(line)
                
                if dialogue_prefix is None:
                    outfile.write(line)
                    outfile.flush()
                    continue

                print(f"处理第 {current_line_num} 行: {text_to_process[:50].strip()}...")
                
                new_text = ""
                # 检查文本是否存在于缓存中
                if text_to_process in translation_cache:
                    new_text = translation_cache[text_to_process]
                    print(f"  -> 命中缓存: {new_text[:50].strip()}...")
                else:
                    # 如果缓存中没有，则调用API
                    new_text = get_gemini_response(gemini_model, text_to_process)
                    print(f"  -> API翻译: {new_text[:50].strip()}...")
                    
                    # 如果API调用成功且返回了与原文不同的内容，则更新缓存
                    if new_text and new_text != text_to_process:
                        translation_cache[text_to_process] = new_text
                        # 将新条目写入缓存文件
                        cache_file.write(f"{text_to_process}{CACHE_DELIMITER}{new_text}\n")
                        cache_file.flush() # 确保立即写入磁盘
                    
                    # 等待一下再进行下一次API调用
                    time.sleep(API_CALL_DELAY)
                
                # 重建行，保留原始样式标签
                # 【行为确认】在这里，每处理完一行（无论是通过缓存还是API），都会立即写入新文件
                new_line = f"{dialogue_prefix},{style_tags}{new_text}\n"
                outfile.write(new_line)
                outfile.flush()

    except FileNotFoundError:
        print(f"错误: 输入文件未找到于 {input_path}")
        return
    except Exception as e:
        print(f"在处理第 {current_line_num} 行时发生意外错误: {e}")
        print("\n处理已停止。您可以稍后从此行恢复。")
        return

    print("\n处理完成!")
    print(f"输出已保存至 {output_path}")


# --- 主程序入口 ---

if __name__ == "__main__":
    if INPUT_ASS_PATH == "YOUR_ASS_FILE_PATH_HERE.ass":
        print("错误: 请先在代码的 '用户配置区域' 设置 'INPUT_ASS_PATH' 变量。")
    else:
        try:
            # 根据输入文件名创建输出文件名
            base, ext = os.path.splitext(INPUT_ASS_PATH)
            output_file = f"{base}_gemini{ext}"

            # 运行主处理函数
            process_ass_file(INPUT_ASS_PATH, output_file, START_LINE)

        except Exception as e:
            print(f"发生未处理的异常: {e}")