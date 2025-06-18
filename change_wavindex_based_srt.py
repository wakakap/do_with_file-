import os
import pysrt
import re # 用于正则表达式处理文本，如删除空格

def process_text_for_comparison(text):
    """
    处理字幕或WAV文件名中的文本，以便进行比较。
    规则：删除"j:", 删除"|"及之后的所有内容, 删除所有空格, 转换为小写。
    """
    # 1. 删除 "j:"
    processed_text = text.replace("j:", "")
    # 2. 删除 "|" 及之后的所有内容 (只分割一次)
    processed_text = processed_text.split('|', 1)[0]
    # 3. 删除所有空格 (包括全角和半角空格)
    # \s+ 匹配一个或多个空白字符（包括空格、制表符、换行符等）
    processed_text = re.sub(r'\s+', '', processed_text)
    # 4. 转换为小写（为了进行不区分大小写的比较）
    processed_text = processed_text.lower()
    return processed_text

def rename_wav_files_by_srt_text(srt_file_path, wav_folder_path):
    """
    根据SRT文件的文本内容，重命名WAV文件的前缀。
    遍历SRT构建文本到序号的映射，然后遍历WAV文件进行匹配和重命名。
    """
    print(f"---- 开始处理 ----")
    print(f"正在读取SRT文件: {srt_file_path}")
    try:
        subs = pysrt.open(srt_file_path, encoding='utf-8')
    except Exception as e:
        print(f"错误：无法打开SRT文件 '{srt_file_path}': {e}")
        return

    # 构建SRT文本到序号的映射
    # 键为处理后的SRT文本，值为SRT序号的0填充字符串（例如 '0001'）
    srt_text_to_index_map = {}
    for sub in subs:
        processed_srt_text = process_text_for_comparison(sub.text)
        srt_index_padded = f"{sub.index:04d}" # 格式化为四位带前导零的字符串 (e.g., 1 -> "0001")
        
        if processed_srt_text in srt_text_to_index_map:
            # 理论上，SRT中的文本应该是独一无二的以匹配唯一的音频段。
            # 如果出现重复，表示SRT内容有歧义，此处只保留最后一个映射，并打印警告。
            print(f"警告：SRT中存在重复的处理后文本 '{processed_srt_text}'。原序号 '{srt_text_to_index_map[processed_srt_text]}' 将被 '{srt_index_padded}' 覆盖。")
        srt_text_to_index_map[processed_srt_text] = srt_index_padded

    print(f"SRT文件解析完成。共发现 {len(srt_text_to_index_map)} 个唯一的处理后文本条目。")
    print(f"正在扫描WAV文件夹: {wav_folder_path}")

    renamed_count = 0
    skipped_count = 0
    not_found_in_srt_count = 0
    already_correctly_named_count = 0

    for filename in os.listdir(wav_folder_path):
        if not filename.lower().endswith('.wav'):
            # 跳过非.wav文件
            continue 

        full_wav_path = os.path.join(wav_folder_path, filename)

        # 尝试解析WAV文件名: 预期格式为 [prefix]_[lang_code]_[text].wav
        # 例如： 0003_zh_今天是个好天气.wav
        
        # 1. 分割文件名和扩展名
        parts = filename.rsplit('.', 1) 
        if len(parts) != 2:
            print(f"跳过 '{filename}'：文件名格式不正确（无文件扩展名）。")
            skipped_count += 1
            continue
        
        name_without_ext = parts[0]
        ext = parts[1]

        # 2. 分割文件名主体，最多分割两次以获取前缀、语言代码和文本部分
        name_parts = name_without_ext.split('_', 2) 
        
        if len(name_parts) < 3:
            print(f"跳过 '{filename}'：文件名格式不正确（缺少'_'分隔符，应至少为 [prefix]_[lang]_[text].wav）。")
            skipped_count += 1
            continue

        current_prefix = name_parts[0]
        lang_code = name_parts[1]
        wav_text_part = name_parts[2]

        processed_wav_text = process_text_for_comparison(wav_text_part)

        # 在SRT映射中查找匹配项
        if processed_wav_text in srt_text_to_index_map:
            matched_srt_index_padded = srt_text_to_index_map[processed_wav_text]
            
            # 构建新的文件名
            new_filename = f"{matched_srt_index_padded}_{lang_code}_{wav_text_part}.{ext}"
            new_full_path = os.path.join(wav_folder_path, new_filename)

            # 只有当新旧路径不同时才执行重命名
            if full_wav_path != new_full_path:
                try:
                    os.rename(full_wav_path, new_full_path)
                    print(f"成功重命名： '{filename}' -> '{new_filename}'")
                    renamed_count += 1
                    # 从映射中删除已使用的SRT索引，确保一对一匹配
                    del srt_text_to_index_map[processed_wav_text]
                except OSError as e:
                    print(f"错误：无法重命名文件 '{filename}' 到 '{new_full_path}': {e}")
                    skipped_count += 1
            else:
                # 文件名已经符合预期，无需重命名
                print(f"'{filename}' 已经具有正确的序号前缀 '{matched_srt_index_padded}'。")
                already_correctly_named_count += 1
                # 即使已经正确命名，也应从映射中删除，避免其被其他WAV文件再次匹配
                del srt_text_to_index_map[processed_wav_text]
        else:
            # 未在SRT中找到匹配的文本
            print(f"未在SRT中找到与 '{filename}' (处理后文本: '{processed_wav_text}') 匹配的文本。")
            not_found_in_srt_count += 1
    
    print("\n--- 重命名操作摘要 ---")
    print(f"成功重命名文件数量： {renamed_count}")
    print(f"已正确命名文件数量： {already_correctly_named_count}")
    print(f"未在SRT中找到匹配的文件数量： {not_found_in_srt_count}")
    print(f"因格式错误或其他原因跳过的文件数量： {skipped_count}")
    print(f"---- 处理完成 ----")

    # 报告未匹配的SRT条目
    if srt_text_to_index_map:
        print("\n--- 未找到对应WAV文件的SRT条目 ---")
        print("以下SRT条目的处理后文本未在任何WAV文件中找到匹配项：")
        for processed_text, srt_index in srt_text_to_index_map.items():
            print(f"  SRT Index: {srt_index}, 处理后文本: '{processed_text}'")

# --- 主执行块 ---
if __name__ == "__main__":
    # --- 请在这里修改你的SRT文件和WAV文件夹的实际路径 ---
    # 示例路径 (请根据你的操作系统和文件位置进行修改):

    # 如果是Windows系统，可以使用原始字符串 (r"...") 来避免反斜杠的转义问题，
    # 或者使用双反斜杠 (\\)
    # srt_file_path = r"C:\Users\YourUser\Documents\MyProject\input.srt"
    # wav_folder_path = r"C:\Users\YourUser\Documents\MyProject\wav_files"

    # 如果是macOS或Linux系统，直接使用正斜杠 (/)
    srt_file_path = "E:\\抽吧唧\\宅男跳舞真抽象\\名前のない怪物\\pr.srt"
    wav_folder_path = "E:\\抽吧唧\\宅男跳舞真抽象\\名前のない怪物\\sub"

    # --- ----------------------------------------------- ---

    # 路径存在性检查，确保文件和文件夹存在且类型正确
    if not os.path.exists(srt_file_path):
        print(f"错误：SRT文件 '{srt_file_path}' 不存在。请检查路径是否正确。")
    elif not os.path.isfile(srt_file_path):
        print(f"错误：'{srt_file_path}' 不是一个文件。请检查路径。")
    elif not os.path.exists(wav_folder_path):
        print(f"错误：WAV文件夹 '{wav_folder_path}' 不存在。请检查路径是否正确。")
    elif not os.path.isdir(wav_folder_path):
        print(f"错误：'{wav_folder_path}' 不是一个文件夹。请检查路径。")
    else:
        # 如果所有路径都有效，则执行重命名操作
        rename_wav_files_by_srt_text(srt_file_path, wav_folder_path)